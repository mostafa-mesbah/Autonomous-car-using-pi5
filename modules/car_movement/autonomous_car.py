from .arduino_handler import ArduinoCarController
from .mission import Mission
class Autonomous_Car:
    def __init__(self,stall_speed,max_speed):
        self.car_stall_speed =stall_speed
        self.max_speed =max_speed
        self.car_stop_speed = 0
        self.mc=ArduinoCarController()
        self.mission=Mission()
    
    def execute_mission(self):
        self.mission.execute_mission(self.mc)
    def update_mission(self,new_missoin):
        return self.mission.update_mission(new_missoin)
        