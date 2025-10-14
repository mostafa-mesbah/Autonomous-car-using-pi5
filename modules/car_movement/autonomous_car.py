from .arduino_controller import ArduinoCarController
from .mission import Mission

class AutonomousCar:
    def __init__(self, stall_speed, max_speed, port='/dev/ttyACM0', baudrate=9600):
        self.stall_speed = stall_speed
        self.max_speed = max_speed
        self.controller = ArduinoCarController(port, baudrate)
        self.mission = Mission()

    def execute_mission(self):
        self.mission.execute(self.controller)

    def update_mission(self, new_mission):
        return self.mission.update(new_mission)

    def stop(self):
        self.controller.stop()
