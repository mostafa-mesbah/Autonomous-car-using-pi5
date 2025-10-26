from .arduino_controller import ArduinoCarController
from .mission import Mission
from  modules.ai_model.model import ModelControl
import threading
class AutonomousCar:
    def __init__(self, stall_speed, max_speed,current_speed, model_path,port='/dev/ttyACM0', baudrate=115200):
        self.stall_speed = stall_speed
        self.current_mission=None
        self.max_speed = max_speed
        self.current_speed=current_speed
        self.model_path=model_path
        self.controller = ArduinoCarController(port, baudrate)
        self.mission = Mission()
        self.model=ModelControl(self.model_path)
        self.stream_thread = None  # Thread placeholder

    def execute_mission(self,given_mission):
        if self.update_mission(given_mission):
            self.mission.execute(self.controller,self.current_mission)

    def update_mission(self, new_mission):
        if self.mission.update(new_mission):
            self.current_mission=new_mission
            return True
    def change_speed(self):
        pass
    def stop(self):
        self.controller.stop()
    def stream_car(self, host="0.0.0.0", port=5000):
            if self.stream_thread is None:
                self.stream_thread = threading.Thread(
                    target=self.model.start_stream, 
                    kwargs={"host": host, "port": port},
                    daemon=True
                )
                self.stream_thread.start()
                print(f"[STREAM] Streaming started in thread on http://{host}:{port}/")