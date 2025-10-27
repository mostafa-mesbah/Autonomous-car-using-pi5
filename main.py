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
            # Process lane detection  
            lane_decision, lane_metric = process_lane(frame,roi_start=200, threshold=40) 
            print(f"[LANE] Metric: {lane_metric:.1f}, Decision: {lane_decision}")
            if lane_decision == 'straight':
                    check_traffic(detections) 
                    car.execute_mission("f")  
            elif lane_decision == 'left':
                    check_traffic(detections)   
                    car.execute_mission("l")  
            elif lane_decision == 'right':
                    check_traffic(detections)   
                    car.execute_mission("r")  

            time.sleep(0.2)  # Small delay to prevent CPU overload


def main():
    global thread_running
    car = AutonomousCar(50, 255, 100, "modules/ai_model/best_from_kaggle_v1.pt")
    
    # Start video stream in a thread
    #car.stream_car()

    # Start detection loop in another thread

    
    # Main thread handles user input
    while True:
        mission_input = input("Enter something or (stop): ")
        print(f"You entered: {mission_input}")
        global latest_mission
        latest_mission = mission_input
        if mission_input.lower() == 'stop':
            print("Goodbye!")
            car.stop()
            break
        
        elif mission_input.startswith("speed="):
            try:
                value = int(mission_input.split('=')[1])
                if 0 <= value <= 255:
                    car.execute_mission(mission_input)
                else:
                    print("❌ Speed must be between 0 and 255.")
            except ValueError:
                print("❌ Invalid speed value. Use: speed=100")

        else:   
                #if mission_input != "s":
                    car.execute_mission(mission_input)
                    thread_running = True
                    detection_thread = threading.Thread(target=detection_loop, args=(car,), daemon=True)
                    detection_thread.start()
                #else:
                    #thread_running = False
                    #car.execute_mission(mission_input)

if __name__ == "__main__":
    main()
