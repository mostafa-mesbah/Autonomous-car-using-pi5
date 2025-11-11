from .arduino_controller import ArduinoCarController
from .mission import Mission
from  modules.ai_model.model import ModelControl
import threading
from ..lane_detector.lane import process_lane
import time
class AutonomousCar:
    def __init__(self, stall_speed=50, max_speed=255,current_speed=100, model_path="modules/ai_model/best_from_kaggle_v1.pt",port='/dev/ttyACM0', baudrate=115200):
        self.stall_speed = stall_speed
        self.current_mission='s'
        self.normal_speed=100
        self.max_speed=max_speed
        self.max_speed = max_speed
        self.current_speed=current_speed
        self.model_path=model_path
        self.stream_thread = None  # Thread placeholder
        self.autonomous_mode_thread = None
        self.stream_thread_running =False
        self.autonomous_mode_thread_running =False
        self.controller = ArduinoCarController(port, baudrate)
        self.mission = Mission()
        self.model=ModelControl(self.model_path)

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
                
    def start_autonomous_mode(self):
        self.autonomous_mode_thread = threading.Thread(target=self.start_autonomous_control,daemon=True)
        self.autonomous_mode_thread_running = True
        self.autonomous_mode_thread.start()
        print("[AUTONOMOUS MODE] Autonomous mode started in thread.")
        while True:
            cc=input().strip().lower()
            if cc == 's':
                self.stop_autonomous_mode()
                break
            else:
                self.execute_mission(cc)


    def stop_autonomous_mode(self):
            self.autonomous_mode_thread_running = False
            self.execute_mission("s")
            self.execute_mission("s")
    
    def capture_frame(self):
        return self.model.capture()
    
    def start_manual_mode(self):
        while True:
            mission_input = input("Enter command: ").strip()
            print(f"You entered: {mission_input}")
            
            latest_mission = mission_input
        
            if mission_input.lower() == 'stop':
                print("Goodbye!")
                thread_running = False
                self.stop()
                break

                #handel turn commands
            elif mission_input.startswith("t ") :
                direction, left_speed, right_speed = self.parse_turn_command(mission_input)
                if direction and left_speed is not None and right_speed is not None:
                    if 0 <= left_speed <= 255 and 0 <= right_speed <= 255:
                        self.execute_mission(mission_input)
                    else:
                        print("❌ Speed values must be between 0 and 255.")
                else:
                    print("❌ Invalid turn command format. Use: 't 150 20' or 't 200 100'")
        
            elif mission_input in ['f', 'b', 's', 'rl', 'rr']:
                self.execute_mission(mission_input)
            
            else:
                print("❌ Unknown command. Type 'help' for available commands.")
                if mission_input.lower() == 'help':
                    print("Available commands: f, b, s, l, r, rl, rr, ls=<value>, rs=<value>, speed=<value>, g, start_auto, stop_auto, stop")

    def parse_turn_command(self,command):
        """Parse turn commands with wheel speeds like 'l 150 20' or 'r 200 100'"""
        parts = command.split()
        if len(parts) == 3:
            try:
                direction = parts[0]
                left_speed = int(parts[1])
                right_speed = int(parts[2])
                return direction, left_speed, right_speed
            except ValueError:
                return None, None, None
        return None, None, None
    
    def start_autonomous_control(self):

        while self.autonomous_mode_thread_running:
            frame = self.capture_frame()
            t0 = time.perf_counter()
            mission, direction, angle = process_lane(frame)
            lane_time = time.perf_counter() - t0
            t1 = time.perf_counter()
            detections = self.model.detect(frame)
            detect_time = time.perf_counter() - t1

            print(f"Detection time: {detect_time*1000:.2f} ms")
            total_time = time.perf_counter() - t0
            fps = 1.0 / total_time if total_time > 0 else 0

            traffic_decision = self.check_traffic(detections)

            if traffic_decision:
                self.execute_mission(traffic_decision)
            else:
                self.execute_mission(mission)
    
    def check_traffic(self,detections):  
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
            
            elif cls == "yellow_sign" and conf > 0.7:  
                print(f"[TRAFFIC] Bump sign detected ({conf:.2f}) - Decision: SLOW DOWN")  
                return "speed=50"  
            
        return None  # No actionable detection

