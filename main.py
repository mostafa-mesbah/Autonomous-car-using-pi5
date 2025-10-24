from modules.car_movement.autonomous_car import AutonomousCar
import threading
import time

def detection_loop(car):
    """Continuously capture frames, detect signs, and take automatic action."""
    while True:
        try:
            frame, detections = car.model.capture_and_detect()
            
            if detections:
                for cls, conf in detections:
                    # Print detections
                    print(f"[DETECTED] {cls} ({conf:.2f})")

                    # Automatic actions based on detection
                    if cls.lower() == "red_light" and conf > 0.6:
                        print("[ACTION] Red light detected! Stopping car...")
                        car.update_mission("s")
                        car.execute_mission()
                    elif cls.lower() == "green_light" and conf > 0.6:
                        print("[ACTION] Green light detected! Moving forward...")
                        car.update_mission("f")
                        car.execute_mission()
                    elif cls.lower() == "bump_sign" and conf > 0.6:
                        print("[ACTION] Bump detected! Slowing down...")
                        car.update_mission("speed=50")
                        car.execute_mission()
                    # Add more rules as needed

        except Exception as e:
            print(f"[DETECTION ERROR] {e}")

        time.sleep(0.2)  # Small delay to prevent CPU overload


def main():
    car = AutonomousCar(50, 255, 100, "modules/ai_model/best_from_kaggle_v1.pt")
    
    # Start video stream in a thread
    car.stream_car()

    # Start detection loop in another thread
    detection_thread = threading.Thread(target=detection_loop, args=(car,), daemon=True)
    #detection_thread.start()
    
    # Main thread handles user input
    while True:
        mission_input = input("Enter something or (stop): ")
        print(f"You entered: {mission_input}")
        
        if mission_input.lower() == 'stop':
            print("Goodbye!")
            car.stop()
            break
        
        elif mission_input.startswith("speed="):
            try:
                value = int(mission_input.split('=')[1])
                if 0 <= value <= 255:
                    if car.update_mission(mission_input):
                        car.execute_mission()
                else:
                    print("❌ Speed must be between 0 and 255.")
            except ValueError:
                print("❌ Invalid speed value. Use: speed=100")

        else:
            if car.update_mission(mission_input):
                car.execute_mission()
            else:
                print("could not update mission")
                print("stopping the car")

if __name__ == "__main__":
    main()
