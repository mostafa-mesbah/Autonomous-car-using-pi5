from .arduino_controller import ArduinoCarController
from .mission import Mission
from  modules.ai_model.model import ModelControl
import threading
from ..lane_detector.lane import process_lane
import time
class AutonomousCar:
    def __init__(self, stall_speed=50, max_speed=255,current_speed=100, model_path="~/graduation_project/Autonomous-car-using-pi5/modules/ai_model/best_traffic_signs.pt",port='/dev/ttyACM0', baudrate=115200):
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
        self.autonomous_mode_lane_running =False
        self.autonomous_mode_traffic_running = False
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
        # allow threads to run
        self.autonomous_mode_lane_running = True
        self.autonomous_mode_traffic_running = True
        # Thread 1: Lane processing
        self.lane_thread = threading.Thread(
            target=self.lane_loop,
            daemon=True
        )

        # Thread 2: Detection + mission
        self.detect_thread = threading.Thread(
            target=self.detect_loop,
            daemon=True
        )

        # Start both threads
        self.lane_thread.start()
        self.detect_thread.start()
        print("[AUTONOMOUS MODE] Lane + Detection threads started.")
        while True:
            cc = input().strip().lower()

            if cc == 's':
                self.stop_autonomous_mode()
                break
            else:
                self.execute_mission(cc)


    def stop_autonomous_mode(self):
            self.autonomous_mode_lane_running = False
            self.autonomous_mode_traffic_running = False
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
            else:
                self.execute_mission(mission_input)
               
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
    
    def lane_loop(self):
        """Only lane processing."""
        while self.autonomous_mode_lane_running:
            frame = self.capture_frame()
            mission, direction, angle = process_lane(frame)
            self.execute_mission(mission)
            


    def detect_loop(self):
        """Capture + detection + mission logic."""
        while self.autonomous_mode_traffic_running:
            frame = self.capture_frame()
            detections = self.model.detect(frame)
            traffic_decision = self.check_traffic(detections)
            if traffic_decision:
                self.execute_mission(traffic_decision)
            else:
                # use latest lane result
                if hasattr(self, "lane_result"):
                    mission, direction, angle = self.lane_result
                    self.execute_mission(mission)
    
    def check_traffic(self, detections):  
        if not detections:  
            return None  
        
        # Process detections with priority (highest confidence first)  
        for cls, conf, verts, box_area in sorted(detections, key=lambda x: x[1], reverse=True):  
            cls = cls.lower()  

            # Only act if area > 5000
            if box_area > 5000:
                if cls == "red_light" and conf > 0.7:  
                    print(f"[TRAFFIC] Red light detected ({conf:.2f}) - Area: {int(box_area)} - Decision: STOP")
                    self.autonomous_mode_lane_running = False  
                    return "s"  

                elif cls == "green_light" and conf > 0.7:  
                    print(f"[TRAFFIC] Green light detected ({conf:.2f}) - Area: {int(box_area)} - Decision: FORWARD")
                    self.autonomous_mode_lane_running = True
                    if not hasattr(self, "lane_thread") or not self.lane_thread.is_alive():
                        self.lane_thread = threading.Thread(target=self.lane_loop, daemon=True)
                        self.lane_thread.start()    
                    return "f"  

                elif cls in ["bump_sign", "yellow_sign"] and conf > 0.7:  
                    print(f"[TRAFFIC] {cls} detected ({conf:.2f}) - Area: {int(box_area)} - Decision: SLOW DOWN")  
                    return "speed=50"  

        return None  # No actionable detection

