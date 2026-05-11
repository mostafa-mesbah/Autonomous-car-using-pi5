#!/usr/bin/env python3
import sys
import termios
import threading
import time

from ..ai_model.detector import TrafficDetector
from ..ai_model.model import ModelControl
from ..camera.capture import CameraCapture
from ..camera.frame_manger import FrameManager
from ..controller.controller import ArduinoCarController
from ..lane_detector.lane import process_lane
from ..missions.mission import Mission
from ..utils.command_queue import CommandQueue
from ..utils.input_handler import InputHandler
from ..logger.logger import CarLogger

class AutonomousCar(InputHandler, TrafficDetector):
    def __init__(
        self,
        stall_speed=50,
        max_speed=255,
        current_speed=100,
        model_path="/home/mostafa/zeft_final/Autonomous-car-using-pi5/Base_arch/fils/best_traffic_signs_openvino_model",
        port="/dev/ttyUSB0",
        baudrate=115200,
    ):
        InputHandler.__init__(self)
        TrafficDetector.__init__(self)
        self.logger = CarLogger()
        self.stall_speed = stall_speed
        self.current_mission = "s"
        self.normal_speed = 150
        self.max_speed = max_speed
        self.current_speed = current_speed
        self.model_path = model_path

        self.stream_thread = None
        self.autonomous_mode_thread = None
        self.capture_thread = None
        self.lane_thread = None
        self.detect_thread = None
        self.stream_thread_running = False
        self.autonomous_mode_lane_running = False
        self.autonomous_mode_traffic_running = False
        self.parking_mode_running = False
        self.waiting_for_parking_response = False

        self.controller = ArduinoCarController(port, baudrate)
        self.mission = Mission()
        self.model = ModelControl(self.model_path)
    
        
        self.camera = CameraCapture()
        self.frame_manager = FrameManager(self.camera, self.logger)
        self.command_queue = CommandQueue()
        self.user_input_queue = self.command_queue.parking_queue
        self.main_thread_commands = self.command_queue.mission_queue
        self.user_command_queue = self.command_queue.user_queue

    def execute_mission(self, given_mission):
        self.current_mission = given_mission
        self.mission.execute(self.controller, given_mission)

    def stop(self):
        self.frame_manager.stop_capture()
        self.controller.stop()

    def stop_all_threads(self):
        """Stop all autonomous threads"""
        print("[STOP] Stopping all threads...")

        self.autonomous_mode_lane_running = False
        self.autonomous_mode_traffic_running = False
        self.parking_mode_running = False
        self.waiting_for_parking_response = False
        self.frame_manager.stop_capture()
        self.command_queue.clear_all()


        print("[STOP] All threads stopped")

    def get_current_frame(self, blocking=False, timeout=0.1):
        return self.frame_manager.get_current_frame(blocking=blocking, timeout=timeout)

    def start_autonomous_mode(self):
        self.autonomous_mode_lane_running = True
        self.autonomous_mode_traffic_running = True
        self.parking_mode_running = False
        self.waiting_for_parking_response = False
        self.traffic_override = False
        self.command_queue.clear_all()

        self.frame_manager.start_capture()

        self.lane_thread = threading.Thread(target=self.lane_loop, daemon=True,name="LaneThread")
        self.detect_thread = threading.Thread(target=self.detect_loop, daemon=True,name="DetectThread")

        self.lane_thread.start()
        self.detect_thread.start()
        print("[AUTONOMOUS MODE] Capture + Lane + Detection threads started.")
        self.execute_mission("f 100")
        # Track last loop time for delay calculation
        last_time = time.perf_counter()

        try:
            while self.autonomous_mode_traffic_running:
                # Calculate delay
                current_time = time.perf_counter()
                delay_ms = (current_time - last_time) * 1000
                
                # Log only the delay
                self.logger.update("cmd_delay_ms", round(delay_ms, 1))
                
                if not self.waiting_for_parking_response:
                    request = self.command_queue.get_parking_request()
                    if request == "parking_request":
                        self.stop_all_threads()
                        self.execute_mission("s")
                        self.waiting_for_parking_response = True

                        print("\n" + "=" * 50)
                        print("PARKING AREA DETECTED!")
                        print("Do you want to park? (y/n): ", end="")
                        sys.stdout.flush()

                        response = self.get_single_key()

                        if response == "y":
                            print("[PARKING] Executing parking command...")
                            self.execute_mission("park")
                            print("[PARKING] Parking command sent. System remains stopped.")
                        else:
                            print("[PARKING] Skipping parking area.")

                        self.waiting_for_parking_response = False
                        print("[INFO] System is stopped. Press Enter to restart autonomous mode or type commands manually.")
                        return
                
                mission_cmd = self.command_queue.get_mission_command()
                if mission_cmd:
                    self.execute_mission(mission_cmd)

                cc = self.get_user_command_non_blocking()
                if cc == "s":
                    self.stop_autonomous_mode()
                    break
                if cc:
                    self.execute_mission(cc)
                
                # Update last time for next delay calculation
                last_time = current_time

        except KeyboardInterrupt:
            self.stop_autonomous_mode()

    def stop_autonomous_mode(self):
        """Stop autonomous mode gracefully"""
        print("[STOP] Stopping autonomous mode...")
        self.stop_all_threads()
        self.execute_mission("s")

    def start_manual_mode(self):
        while True:
            mission_input = input("Enter command: ").strip()
            print(f"You entered: {mission_input}")

            if mission_input.lower() == "stop":
                print("Goodbye!")
                self.stop()
                break

            self.execute_mission(mission_input)

    
    def lane_loop(self):
        last_time = time.perf_counter()  # Track last iteration time
        
        while self.autonomous_mode_lane_running:
            try:
                # Calculate delay since last loop iteration
                current_time = time.perf_counter()
                delay_ms = (current_time - last_time) * 1000
                
                # Log the delay (once per loop)
                self.logger.update("lane_delay_ms", round(delay_ms, 1))
                
                if self.should_override_lane():
                    last_time = current_time  # Update time even when skipping
                    continue

                frame = self.get_current_frame()
                if frame is not None:
                    mission, direction, angle, debug_info = process_lane(frame)
                    self.main_thread_commands.put(mission)

                # Update last time for next delay calculation
                last_time = current_time

            except Exception as e:
                print(f"[LANE] Error: {e}")
    def detect_loop(self):
        last_time = time.perf_counter()

        while self.autonomous_mode_traffic_running:
            current_time = time.perf_counter()
            delay_ms = (current_time - last_time) * 1000
            self.logger.update("detect_delay_ms", round(delay_ms, 1))
            
            try:
                if self.parking_mode_running or self.waiting_for_parking_response:
                    last_time = current_time
                    continue

                frame = self.get_current_frame()
                if frame is not None:
                    detections = self.model.detect(frame)
                    traffic_decision, detection_type = self.check_traffic(detections)

                    if traffic_decision:
                        # Handle red light - DEACTIVATE lane loop
                        if detection_type == "red_light" or (detection_type == "red_light_active" and self.is_red_light_active()):
                            if self.autonomous_mode_lane_running:
                                print("[TRAFFIC] 🛑 Red light - DEACTIVATING lane detection")
                                self.autonomous_mode_lane_running = False
                            self.main_thread_commands.put("s")  # Stop command
                        
                        # Handle green light - REACTIVATE lane loop
                        elif detection_type == "green_light":
                            if not self.autonomous_mode_lane_running:
                                print("[TRAFFIC] 🟢 Green light - REACTIVATING lane detection")
                                self.autonomous_mode_lane_running = True
                                # Create NEW thread instead of restarting old one
                                self.lane_thread = threading.Thread(target=self.lane_loop, daemon=True,name="LaneThread")
                                self.lane_thread.start()
                            self.main_thread_commands.put("f")  # Forward command
                        
                        # Handle parking
                        elif traffic_decision == "park" and not self.waiting_for_parking_response:
                            self.user_input_queue.put("parking_request")
                        
                        # Handle other traffic signs
                        elif traffic_decision not in ["s", "f"]:  # speed limits, bumps, etc.
                            self.main_thread_commands.put(traffic_decision)
                
                last_time = current_time
                
            except Exception as e:
                print(f"[DETECT] Error: {e}")
                import traceback
                traceback.print_exc()

        return None