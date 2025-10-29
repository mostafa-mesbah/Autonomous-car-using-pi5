from modules.car_movement.autonomous_car import AutonomousCar
from modules.lane_detector.lane import process_lane
import threading
import time

thread_running = False
latest_mission = None

def check_traffic(detections):  
    """  
    Process traffic sign detections and return a decision.  
      
    Args:  
        detections: List of tuples (class_name, confidence) from model  
          
    Returns:  
        str: Mission command ('s', 'f', 'speed=50', etc.) or None  
    """  
    if not detections:  
        return None  
      
    # Process detections with priority (highest confidence first)  
    for cls, conf in sorted(detections, key=lambda x: x[1], reverse=True):  
        cls = cls.lower()  
          
        if cls == "red_light" and conf > 0.7:  
            print(f"[TRAFFIC] Red light detected ({conf:.2f}) - Decision: STOP")  
            return "s"  
          
        elif cls == "green_light" and conf > 0.7:  
            print(f"[TRAFFIC] Green light detected ({conf:.2f}) - Decision: FORWARD")  
            return "f"  
          
        elif cls == "bump_sign" and conf > 0.7:  
            print(f"[TRAFFIC] Bump sign detected ({conf:.2f}) - Decision: SLOW DOWN")  
            return "speed=50"  
          
        # Add more traffic signs here  
          
    return None  # No actionable detection

def detection_loop(car):
    """Continuously capture frames, detect signs, and take automatic action."""
    global latest_mission
    global thread_running
    
    while thread_running:
        frame, detections = car.model.capture_and_detect()
        
        # Process lane detection - now returns decision and wheel speeds
        lane_decision,  right_speed, left_speed= process_lane(frame) 
        print(f"Lane Decision: {lane_decision}, L: {left_speed}, R: {right_speed}")
        
        # Check traffic signs first (higher priority)
        traffic_decision = check_traffic(detections)
        
        if traffic_decision:
            # Traffic sign has priority
            car.execute_mission(traffic_decision)
            print(f"Traffic Decision: {traffic_decision}")
        else:
            # Follow lane detection with calculated wheel speeds
            if lane_decision == 'straight':
                # Use the calculated speeds for straight driving
                car.execute_mission(f"t {left_speed} {right_speed}")  
            elif lane_decision == 'left':
                # Use the calculated speeds for left turn
                car.execute_mission(f"t {left_speed} {right_speed}")
            elif lane_decision == 'right':
                # Use the calculated speeds for right turn
                car.execute_mission(f"t {left_speed} {right_speed}")


def parse_turn_command(command):
    """Parse turn commands with wheel speeds like 'l 150 20' or 'r 200 100'"""
    parts = command.split()
    if len(parts) == 3:
        try:
            direction = parts[0]
            left_speed = int(parts[1])
            right_speed = int(parts[2])
            return direction, left_speed, right_speed
        except ValueError:
            return None, None, None
    return None, None, None

def main():
    global thread_running
    car = AutonomousCar(50, 255, 100, "modules/ai_model/best_from_kaggle_v1.pt")
    
    print("Available commands:")
    print("  f, b, s, l, r, rl, rr - Basic movements")
    print("  l <left_pwm> <right_pwm> - Turn left with specific speeds (e.g., 'l 150 20')")
    print("  r <left_pwm> <right_pwm> - Turn right with specific speeds (e.g., 'r 200 100')")
    print("  ls=<value> - Set left wheel speed")
    print("  rs=<value> - Set right wheel speed") 
    print("  both=<value> - Set both wheel speeds")
    print("  speed=<value> - Set both speeds (alias for both)")
    print("  g - Toggle GPS mode")
    print("  stop - Exit program")
    print("  start_auto - Start autonomous lane following")
    print("  stop_auto - Stop autonomous lane following")
    
    while True:
        mission_input = input("Enter command: ").strip()
        print(f"You entered: {mission_input}")
        
        global latest_mission
        latest_mission = mission_input
        
        if mission_input.lower() == 'stop':
            print("Goodbye!")
            thread_running = False
            car.stop()
            break
        
        elif mission_input.lower() == 'sa':
            if not thread_running:
                thread_running = True
                detection_thread = threading.Thread(target=detection_loop, args=(car,), daemon=True)
                detection_thread.start()
                print("🟢 Autonomous lane following STARTED")
            else:
                print("🟡 Autonomous mode already running")
        
        elif mission_input.lower() == 'sta':
            thread_running = False
            print("🔴 Autonomous lane following STOPPED")
        
        # Handle turn commands with wheel speeds
        elif mission_input.startswith("t ") :
            direction, left_speed, right_speed = parse_turn_command(mission_input)
            if direction and left_speed is not None and right_speed is not None:
                if 0 <= left_speed <= 255 and 0 <= right_speed <= 255:
                    car.execute_mission(mission_input)
                else:
                    print("❌ Speed values must be between 0 and 255.")
            else:
                print("❌ Invalid turn command format. Use: 'l 150 20' or 'r 200 100'")
        
        # Handle speed commands
        elif mission_input.startswith("speed=") or mission_input.startswith("both="):
            try:
                if mission_input.startswith("speed="):
                    value = int(mission_input.split('=')[1])
                else:  # both=
                    value = int(mission_input.split('=')[1])
                    
                if 0 <= value <= 255:
                    car.execute_mission(mission_input)
                else:
                    print("❌ Speed must be between 0 and 255.")
            except ValueError:
                print("❌ Invalid speed value. Use: 'speed=100' or 'both=100'")
        
        elif mission_input.startswith("ls=") or mission_input.startswith("rs="):
            try:
                value = int(mission_input.split('=')[1])
                if 0 <= value <= 255:
                    car.execute_mission(mission_input)
                else:
                    print("❌ Speed must be between 0 and 255.")
            except ValueError:
                print("❌ Invalid speed value. Use: 'ls=100' or 'rs=100'")
        
        # Handle basic movement commands
        elif mission_input in ['f', 'b', 's', 'l', 'r', 'rl', 'rr', 'g']:
            car.execute_mission(mission_input)
        
        else:
            print("❌ Unknown command. Type 'help' for available commands.")
            if mission_input.lower() == 'help':
                print("Available commands: f, b, s, l, r, rl, rr, ls=<value>, rs=<value>, both=<value>, speed=<value>, g, start_auto, stop_auto, stop")

if __name__ == "__main__":
    main()