from modules.car_movement.autonomous_car import AutonomousCar
from modules.lane_detector.lane import process_lane
import threading
import time

thread_running = False
latest_mission = None


    
    



def main():
    global thread_running
    car = AutonomousCar(50, 255, 100, "modules/ai_model/best_from_kaggle_v1.pt")
    #greetings

    while True:
        print("Good day! Welcome to the Autonomous Car Control System.")
        print("please select manual mood or autonomous mood")
        print("for manual mode type 'm' and for autonomous mode type 'a'")
        cc=input().strip().lower()
        if cc == 'a':

            print("You have selected autonomous mode.")
            print("to start press \"s\"")

            if input().strip().lower() == 's':
                car.start_autonomous_mode()
                print("🟢 Autonomous lane following STARTED")

        elif cc == 'm':
            print("You have selected manual mode.")
            car.start_manual_mode()
        
if __name__ == "__main__":
    main()