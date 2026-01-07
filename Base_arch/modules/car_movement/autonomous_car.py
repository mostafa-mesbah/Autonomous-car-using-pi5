#!/usr/bin/env python3
from .arduino_controller import ArduinoCarController
from .mission import Mission
from modules.ai_model.model import ModelControl
import threading
from ..lane_detector.lane import process_lane
import time
import queue
import sys
import termios
import tty

class AutonomousCar:
    def __init__(self, stall_speed=50, max_speed=255, current_speed=100, 
                 model_path="~/graduation_project/Autonomous-car-using-pi5/modules/ai_model/best_traffic_signs.pt",
                 port='/dev/ttyACM0', baudrate=115200):
        self.stall_speed = stall_speed
        self.current_mission = 's'
        self.normal_speed = 100
        self.max_speed = max_speed
        self.current_speed = current_speed
        self.model_path = model_path
        self.stream_thread = None
        self.autonomous_mode_thread = None
        self.stream_thread_running = False
        self.autonomous_mode_lane_running = False
        self.autonomous_mode_traffic_running = False
        self.parking_mode_running = False
        self.controller = ArduinoCarController(port, baudrate)
        self.mission = Mission()
        self.model = ModelControl(self.model_path)
        self.user_input_queue = queue.Queue()
        self.main_thread_commands = queue.Queue()
        self.original_term_settings = None
        self.waiting_for_parking_response = False  # NEW: Track if waiting for parking response
        self.traffic_override = False

    def execute_mission(self, given_mission):
        if self.update_mission(given_mission):
            self.mission.execute(self.controller, self.current_mission)

    def update_mission(self, new_mission):
        if self.mission.update(new_mission):
            self.current_mission = new_mission
            return True
        return False

    def stop(self):
        self.controller.stop()

    def get_single_key(self, prompt=None):
        """Get a single key press without waiting for Enter"""
        if prompt:
            sys.stdout.write(prompt)
            sys.stdout.flush()
        
        # Set terminal to raw mode temporarily
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        # Echo the key pressed and newline
        sys.stdout.write(key + '\n')
        sys.stdout.flush()
        
        return key

    def stop_all_threads(self):
        """Stop all autonomous threads"""
        print("[STOP] Stopping all threads...")
        
        self.autonomous_mode_lane_running = False
        self.autonomous_mode_traffic_running = False
        self.parking_mode_running = False
        
        # Give threads a moment to exit
        time.sleep(0.2)
        
        print("[STOP] All threads stopped")

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
        # Reset flags
        self.autonomous_mode_lane_running = True
        self.autonomous_mode_traffic_running = True
        self.parking_mode_running = False
        self.waiting_for_parking_response = False
        
        # Clear queues
        while not self.user_input_queue.empty():
            self.user_input_queue.get()
        while not self.main_thread_commands.empty():
            self.main_thread_commands.get()
        
        # Start threads
        self.lane_thread = threading.Thread(
            target=self.lane_loop,
            daemon=True
        )
        
        self.detect_thread = threading.Thread(
            target=self.detect_loop,
            daemon=True
        )
        
        self.lane_thread.start()
        self.detect_thread.start()
        print("[AUTONOMOUS MODE] Lane + Detection threads started.")
        
        # Main control loop
        try:
            while self.autonomous_mode_traffic_running:
                # Check for parking requests
                if not self.waiting_for_parking_response:
                    try:
                        if self.user_input_queue.qsize() > 0:
                            request = self.user_input_queue.get_nowait()
                            if request == "parking_request":
                                # Stop all threads and car
                                self.stop_all_threads()
                                self.execute_mission("s")
                                self.waiting_for_parking_response = True
                                
                                # Ask for parking confirmation
                                print("\n" + "="*50)
                                print("PARKING AREA DETECTED!")
                                print("Do you want to park? (y/n): ", end="")
                                sys.stdout.flush()
                                
                                # Get single key without Enter
                                response = self.get_single_key()
                                
                                if response == 'y':
                                    print("[PARKING] Executing parking command...")
                                    # Just send the park command and stay stopped
                                    self.execute_mission("park")
                                    print("[PARKING] Parking command sent. System remains stopped.")
                                else:
                                    print("[PARKING] Skipping parking area.")
                                
                                # Reset flag but don't restart threads
                                self.waiting_for_parking_response = False
                                print("[INFO] System is stopped. Press Enter to restart autonomous mode or type commands manually.")
                                # System stays stopped - user needs to manually restart
                                return  # Exit autonomous mode
                    except queue.Empty:
                        pass
                
                # Execute mission commands from detection thread
                try:
                    mission_cmd = self.main_thread_commands.get(timeout=0.1)
                    self.execute_mission(mission_cmd)
                except queue.Empty:
                    pass
                
                # Check for user input (non-blocking with select)
                import select
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    cc = sys.stdin.readline().strip().lower()
                    if cc == 's':
                        self.stop_autonomous_mode()
                        break
                    elif cc:
                        self.execute_mission(cc)
                        
        except KeyboardInterrupt:
            self.stop_autonomous_mode()
        finally:
            # Clean up terminal if needed
            if self.original_term_settings:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_term_settings)

    def stop_autonomous_mode(self):
        """Stop autonomous mode gracefully"""
        print("[STOP] Stopping autonomous mode...")
        self.stop_all_threads()
        self.execute_mission("s")

    def capture_frame(self):
        return self.model.capture()

    def start_manual_mode(self):
        while True:
            mission_input = input("Enter command: ").strip()
            print(f"You entered: {mission_input}")
            
            if mission_input.lower() == 'stop':
                print("Goodbye!")
                self.stop()
                break
            else:
                self.execute_mission(mission_input)

    def lane_loop(self):
        while self.autonomous_mode_lane_running:
            try:
                if self.traffic_override:
                    time.sleep(0.05)
                    continue   # ❗ DO NOT SEND LANE COMMANDS

                frame = self.capture_frame()
                if frame is not None:
                    mission, direction, angle = process_lane(frame)
                    self.main_thread_commands.put(mission)

                time.sleep(0.05)
            except Exception as e:
                print(f"[LANE] Error: {e}")
                time.sleep(0.1)

    def detect_loop(self):
        """Capture + detection + mission logic."""
        while self.autonomous_mode_traffic_running:
            try:
                if self.parking_mode_running or self.waiting_for_parking_response:
                    time.sleep(0.1)
                    continue
                    
                frame = self.capture_frame()
                if frame is not None:
                    detections = self.model.detect(frame)
                    traffic_decision = self.check_traffic(detections)
                    
                    if traffic_decision:
                        if traffic_decision == "park" and not self.waiting_for_parking_response:
                            # Request parking decision
                            self.user_input_queue.put("parking_request")
                        elif traffic_decision != "park":
                            self.main_thread_commands.put(traffic_decision)
                            
                time.sleep(0.1)
            except Exception as e:
                print(f"[DETECT] Error: {e}")
                time.sleep(0.1)

    def check_traffic(self, detections):  
        if not detections:  
            return None  
        
        # Process detections with priority (highest confidence first)  
        for cls, conf, verts, box_area in sorted(detections, key=lambda x: x[1], reverse=True):  
            cls = cls.lower()  

            if box_area > 5000:
                if cls == "red_light" and conf > 0.7:  
                    print(f"[TRAFFIC] Red light detected ({conf:.2f}) - Area: {int(box_area)} - Decision: STOP")
                    self.traffic_override = True
                    return "s"  

                elif cls == "green_light" and conf > 0.7:  
                    print(f"[TRAFFIC] Green light detected ({conf:.2f}) - Area: {int(box_area)} - Decision: FORWARD")
                    self.traffic_override = False
                    return "f"  

                elif cls in ["bump_sign", "yellow_sign"] and conf > 0.7:  
                    print(f"[TRAFFIC] {cls} detected ({conf:.2f}) - Area: {int(box_area)} - Decision: SLOW DOWN")  
                    return "speed=50"  
                
                elif cls == "parking_area" and conf > 0.7:  
                    print(f"[TRAFFIC] Parking area detected ({conf:.2f}) - Area: {int(box_area)}")
                    return "park"
                
        return None