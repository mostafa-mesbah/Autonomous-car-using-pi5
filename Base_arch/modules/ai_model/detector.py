class TrafficDetector:
    """Stateless detection checker for all models — state lives in AutonomousCar"""

    SPEED_LIMIT_NAMES = {
        "speed limit 10": 10,  "speed limit 20": 20,  "speed limit 30": 30,
        "speed limit 40": 40,  "speed limit 50": 50,  "speed limit 60": 60,
        "speed limit 70": 70,  "speed limit 80": 80,  "speed limit 90": 90,
        "speed limit 100": 100, "speed limit 110": 110, "speed limit 120": 120,
        "speed limit 130": 130,
    }

    STOP_CLASS_NAMES = {   ## "person"
        "bicycle", "car", "motorcycle",
        "bus", "train", "truck", "stop sign"
    }

    def check_traffic(self, detections):
        if not detections:
            return None, None

        for cls, conf, verts, box_area in sorted(detections, key=lambda x: x[1], reverse=True):
            cls = cls.lower()
            if box_area > 1400:
                if cls == "red_light" and conf > 0.6:
                    print(f"[TRAFFIC] 🔴 RED LIGHT detected ({conf:.2f})")
                    return "s", "red_light"

                elif cls == "green_light" and conf > 0.6:
                    print(f"[TRAFFIC] 🟢 GREEN LIGHT detected ({conf:.2f})")
                    return "f", "green_light"

                elif cls in ("bump_sign", "yellow_light") and conf > 0.6:
                    print(f"[TRAFFIC] {cls} detected ({conf:.2f}) - SLOW DOWN")
                    return "f 50", cls

                elif cls == "parking_area" and conf > 0.7:
                    print(f"[TRAFFIC] Parking area detected ({conf:.2f})")
                    return "park", "parking_area"

        return None, None

    def check_speed(self, detections):
        if not detections:
            return None, None

        best = max(detections, key=lambda x: x[1])
        cls, conf, verts, box_area = best
        cls = cls.lower()

        if cls in self.SPEED_LIMIT_NAMES:
            limit = self.SPEED_LIMIT_NAMES[cls]
            print(f"[SPEED] Speed limit {limit} detected ({conf:.2f})")
            return f"f {limit}", "speed_limit"

        return None, None

    def check_general(self, detections):
        if not detections:
            return None, None

        for cls, conf, verts, box_area in sorted(detections, key=lambda x: x[1], reverse=True):
            cls = cls.lower()
            if cls in self.STOP_CLASS_NAMES and conf > 0.8:
                print(f"[GENERAL] 🚗 Stop-class detected: {cls} ({conf:.2f})")
                return "s", cls
            

        return "f", "clear"