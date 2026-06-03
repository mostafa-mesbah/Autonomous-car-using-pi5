# modules/ai_model/detector.py
class TrafficDetector:
    """Handles traffic sign detection and decisions"""
    
    def __init__(self):
        self.traffic_override = False
        self.parking_mode_running = False
        self.waiting_for_parking_response = False
        self.red_light_active = False
    
    def check_traffic(self, detections):
        """
        Process detections and return (decision, detection_type)
        
        Returns:
            tuple: (decision, detection_type)
            decision: "s", "f", "speed=50", "park", None
            detection_type: "red_light", "green_light", "bump_sign", "parking_area", None
        """
        if not detections:
            # If red light was active and we see nothing, stay stopped
            if self.red_light_active:
                print("[TRAFFIC] Waiting at red light...")
                return "s", "red_light_active"
            return None, None
        
        # Process detections with priority (highest confidence first)
        for cls, conf, verts, box_area in sorted(detections, key=lambda x: x[1], reverse=True):
            cls = cls.lower()
            
            if box_area > 1400:
                if cls == "red_light" and conf > 0.7:
                    print(f"[TRAFFIC] 🔴 RED LIGHT detected ({conf:.2f})")
                    self.red_light_active = True
                    self.traffic_override = True
                    return "s", "red_light"
                
                elif cls == "green_light" and conf > 0.7:
                    print(f"[TRAFFIC] 🟢 GREEN LIGHT detected ({conf:.2f})")
                    self.red_light_active = False
                    self.traffic_override = False
                    return "f", "green_light"
                
                elif cls in ["bump_sign", "yellow_sign"] and conf > 0.7:
                    print(f"[TRAFFIC] {cls} detected ({conf:.2f}) - SLOW DOWN")
                    return "speed=50", cls
                
                elif cls == "parking_area" and conf > 0.7:
                    print(f"[TRAFFIC] Parking area detected ({conf:.2f})")
                    return "park", "parking_area"
                
                elif cls == "yellow_light" and conf > 0.7:
                    print(f"[TRAFFIC] Yellow light detected ({conf:.2f})")
                    return "speed=50", "yellow_light"
        
        # If red light was active but no detection in this frame
        if self.red_light_active:
            return "s", "red_light_active"
        
        return None, None
    
    def should_override_lane(self):
        """Check if lane detection should be overridden"""
        return self.traffic_override or self.red_light_active
    
    def is_red_light_active(self):
        """Check if currently stopped at red light"""
        return self.red_light_active
    
    def clear_red_light(self):
        """Manually clear red light state"""
        self.red_light_active = False
        self.traffic_override = False