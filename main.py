#!/usr/bin/env python3
from modules.car_movement.autonomous_car import AutonomousCar
from modules.lane_detector.lane import process_lane
import threading
import time
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
def main():
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "modules", "ai_model", "best_traffic_signs.pt")
    car = AutonomousCar(50, 255, 100, model_path)
    car.stream_car()

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