#!/usr/bin/env python3
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from modules.car_movement import AutonomousCar
from modules.web_app.sync_to_app import TelemetrySyncClient
def main():

    car = AutonomousCar(50, 255, 150)
    sync_client = TelemetrySyncClient(server_url="http://68.183.216.141:5001", 
                                   data_file_path="/home/uav/grad/Autonomous-car-using-pi5/Base_arch/fils/car_telemetry.json", debug=False)
    sync_client.start()

    while True:
        print("Good day! Welcome to the Autonomous Car Control System.")
        print("please select manual mood or autonomous mood")
        print("for manual mode type 'm' and for autonomous mode type 'a'")
        cc=input().strip().lower()
        if cc == 'a':

            print("You have selected autonomous mode.")
            print("to start press \"s\"")

            if input().strip().lower() == 's':
                print("🟢 Autonomous lane following STARTED")
                car.start_autonomous_mode()
                

        elif cc == 'm':
            print("You have selected manual mode.")
            car.start_manual_mode()
        
if __name__ == "__main__":
    main()
