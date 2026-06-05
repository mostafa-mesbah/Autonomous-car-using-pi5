#!/usr/bin/env python3
"""
car_simulator.py  —  Updated to match Base_arch real output

Real YOLO class names from check_traffic() in autonomous_car.py:
  red_light · green_light · bump_sign · yellow_sign · parking_area

Real mission commands from mission.py:
  f · b · s · t {servo_angle} · speed=50 · park

Servo angles from lane.py:
  SERVO_LEFT=66  SERVO_CENTER=86  SERVO_RIGHT=110

New fields added to telemetry (all coordinated with dashboard_v2.html):
  traffic_light    : "red" | "green" | "none"
  detected_sign    : "bump" | "caution" | "parking" | "none"
  pedestrian       : true | false   (human detection → car stops)
  yolo_confidence  : float 0-100
  servo_angle      : int 66-110     (from lane.py steering)
  traffic_override : bool           (True when traffic overrides lane)
  mission          : str            (last mission command sent)
"""

import json, time, random, sys

def load_config():
    try:
        with open('config.json') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found!"); sys.exit(1)


def simulate_yolo():
    """
    REPLACE this entire function with real output from ModelControl.detect()

    In autonomous_car.py your check_traffic() returns these strings:
        "s"          → red light
        "f"          → green light
        "speed=50"   → bump_sign or yellow_sign
        "park"       → parking_area
        None         → nothing detected

    Map that to the dashboard fields below.
    """
    roll = random.random()

    if roll < 0.55:
        return dict(traffic_light="none", detected_sign="none",
                    pedestrian=False, yolo_confidence=0.0,
                    traffic_override=False, mission="f 100")

    elif roll < 0.67:
        conf = round(random.uniform(70, 99), 1)
        return dict(traffic_light="red", detected_sign="none",
                    pedestrian=False, yolo_confidence=conf,
                    traffic_override=True, mission="s")

    elif roll < 0.76:
        conf = round(random.uniform(70, 99), 1)
        return dict(traffic_light="green", detected_sign="none",
                    pedestrian=False, yolo_confidence=conf,
                    traffic_override=False, mission="f 150")

    elif roll < 0.83:
        # bump_sign or yellow_sign → speed=50
        sign = random.choice(["bump", "caution"])
        conf = round(random.uniform(70, 95), 1)
        return dict(traffic_light="none", detected_sign=sign,
                    pedestrian=False, yolo_confidence=conf,
                    traffic_override=False, mission="speed=50")

    elif roll < 0.90:
        # parking_area
        conf = round(random.uniform(75, 98), 1)
        return dict(traffic_light="none", detected_sign="parking",
                    pedestrian=False, yolo_confidence=conf,
                    traffic_override=False, mission="park")

    else:
        # Pedestrian detected → emergency stop
        conf = round(random.uniform(88, 99), 1)
        return dict(traffic_light="none", detected_sign="none",
                    pedestrian=True, yolo_confidence=conf,
                    traffic_override=True, mission="s")


def simulate_lane():
    """
    REPLACE with real output from process_lane() in lane.py

    process_lane() returns:
        "t {servo_angle}"  e.g. "t 86", "t 72", "t 104"
        "s"                if no lines detected

    Servo range: 66 (full left) → 86 (centre) → 110 (full right)
    """
    # Random walk around centre
    angle = random.gauss(86, 10)
    angle = max(66, min(110, round(angle)))
    return angle


def simulate_sensors():
    """REPLACE with real Arduino sensor reads.
    Speed is Arduino PWM (0-255), NOT km/h — this is a model car.
    Normal driving: ~100-150 PWM. Slow (bump): 50 PWM. Stopped: 0.
    """
    # Simulate PWM motor value: mostly driving (100-150), occasionally stopped
    import random as _r
    if _r.random() < 0.1:
        speed = 0.0         # stopped (red light / idle)
    elif _r.random() < 0.15:
        speed = 50.0        # slow (bump detected)
    else:
        speed = _r.uniform(90, 155)  # normal forward driving range
    battery = max(5, 100 - _r.uniform(0, 0.5))
    temp    = _r.uniform(25, 40)
    return round(speed, 1), round(battery, 1), round(temp, 1)


def update_telemetry(config, speed, battery, temp, lat, lon, yolo, servo_angle):
    """Write full telemetry JSON that matches dashboard_v2.html expectations."""

    # Speed 0 when stopped (red light, pedestrian, mission='s')
    if yolo['pedestrian'] or yolo['traffic_light'] == 'red' or yolo.get('mission') == 's':
        effective_speed = 0.0
    elif yolo['detected_sign'] in ('bump', 'caution'):
        effective_speed = 50.0  # bump → slow PWM
    else:
        effective_speed = speed

    data = {
        "car_id":      config['car_id'],
        "speed":       round(effective_speed, 1),
        "battery":     round(battery, 1),
        "temperature": round(temp, 1),
        "gps": {
            "lat": round(lat, 6),
            "lon": round(lon, 6)
        },
        "crash":  False,
        "mode":   "auto",

        # YOLO fields — matching real class names from autonomous_car.py
        "traffic_light":    yolo['traffic_light'],   # "red"|"green"|"none"
        "detected_sign":    yolo['detected_sign'],   # "bump"|"caution"|"parking"|"none"
        "pedestrian":       yolo['pedestrian'],      # bool
        "yolo_confidence":  yolo['yolo_confidence'], # 0-100
        "traffic_override": yolo['traffic_override'],# bool
        "mission":          yolo['mission'],         # last command string

        # Lane / steering fields from lane.py
        "servo_angle": servo_angle,  # 66-110, centre=86

        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    data_file = config.get('data_file', 'car_telemetry.json')
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)

    # Also POST directly to backend — bypasses sync_to_server.py
    try:
        import requests as _req
        server = config.get('server_url', 'http://localhost:5000')
        _req.post(f"{server}/api/telemetry", json=data, timeout=1)
    except Exception:
        pass  # server not running yet — file write is enough

    return data


def main():
    config = load_config()
    lat    = config['starting_position']['lat']
    lon    = config['starting_position']['lon']

    print(f"Simulator starting — {config['car_id']}")
    print(f"Writing to: {config.get('data_file','car_telemetry.json')}")
    print("-" * 55)

    try:
        i = 0
        while True:
            i += 1
            speed, battery, temp = simulate_sensors()
            lat += random.uniform(-0.0001, 0.0001)
            lon += random.uniform(-0.0001, 0.0001)

            yolo         = simulate_yolo()
            servo_angle  = simulate_lane()

            data = update_telemetry(config, speed, battery, temp,
                                    lat, lon, yolo, servo_angle)

            if config.get('debug', True):
                tags = []
                if yolo['traffic_light'] != 'none': tags.append(f"Light:{yolo['traffic_light']}")
                if yolo['detected_sign'] != 'none':  tags.append(f"Sign:{yolo['detected_sign']}")
                if yolo['pedestrian']:               tags.append("PEDESTRIAN")
                tag_str = ' | '.join(tags) if tags else ''
                print(f"[{i:04d}] PWM:{data['speed']:5.1f} "
                      f"bat:{battery:5.1f}% tmp:{temp:4.1f}°C "
                      f"servo:{servo_angle}° {tag_str}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nSimulator stopped")


if __name__ == "__main__":
    main()
