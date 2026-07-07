#!/usr/bin/env python3
import sys
import termios
import threading
import time

import serial

from ..ai_model.detector import TrafficDetector
from ..ai_model.model import ModelControl
from ..camera.capture import CameraCapture
from ..camera.frame_manger import FrameManager
from ..controller.controller import ArduinoCarController
from ..controller.esp32 import ESP32Sensor
from ..lane_detector.lane import process_lane
from ..missions.mission import Mission
from ..utils.command_queue import CommandQueue
from ..utils.input_handler import InputHandler
from .steer_smoother import SteeringSmoother
from ..telemetry import TelemetryData
from ..utils.temp_monitor import Temp_monitor
class AutonomousCar(InputHandler, TrafficDetector):
    def __init__(
        self,
        stall_speed=50,
        max_speed=255,
        current_speed=100,
        traffic_model_path="/home/uav/grad/Autonomous-car-using-pi5/Base_arch/fils/best_traffic_signs_openvino_model",
        speed_model_path="/home/uav/grad/Autonomous-car-using-pi5/Base_arch/fils/best_speed_limits_openvino_model",
        general_model_path="/home/uav/grad/Autonomous-car-using-pi5/Base_arch/fils/multible_things_openvino_model",
        port="/dev/ttyACM0",
        esp32_port="/dev/ttyUSB0",
        baudrate=115200,
    ):
        InputHandler.__init__(self)
        TrafficDetector.__init__(self)
        self.red_light_active = False
        self.stall_speed = stall_speed
        self.current_mission = "s"
        self.normal_speed = 100
        self.max_speed = max_speed
        self.current_speed = current_speed
        self.traffic_model_path = traffic_model_path
        self.speed_model_path = speed_model_path
        self.general_model_path = general_model_path

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
        self.telemetry = TelemetryData()
        self.mission = Mission(telemetry=self.telemetry)
        self.traffic_model = ModelControl(self.traffic_model_path)
        self.speed_model = ModelControl(self.speed_model_path)
        self.general_model = ModelControl(self.general_model_path)
        self.steer_smoother = SteeringSmoother()
        
        self.camera = CameraCapture()
        self.command_queue = CommandQueue()
        self.user_input_queue = self.command_queue.parking_queue
        self.main_thread_commands = self.command_queue.mission_queue
        self.user_command_queue = self.command_queue.user_queue
        self.frame_manager = FrameManager(self.camera)
        self.esp32 = ESP32Sensor(port=esp32_port, baudrate=baudrate)
        self.temp_monitor = Temp_monitor()
    
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
        self.command_queue.clear_all()

        self.frame_manager.start_capture()

        self.lane_thread = threading.Thread(target=self.lane_loop, daemon=True, name="LaneThread")
        self.detect_thread = threading.Thread(target=self.detect_loop, daemon=True, name="DetectThread")

        self.lane_thread.start()
        self.detect_thread.start()
        print("[AUTONOMOUS MODE] Capture + Lane + Detection threads started.")
        self.execute_mission("f 100")
        self.execute_mission("flashoff")
        self.telemetry.update("crash", False)
        # Track last loop time for delay calculation
        last_time = time.perf_counter()

        try:
            while self.autonomous_mode_traffic_running:
                self.telemetry.update("temperature", self.temp_monitor.get_temp())
                # ── 1. SAFETY FIRST: CRASH CHECK ──────────────────────────────
                if self.esp32.is_crash_detected():
                    print("\n" + "!" * 60)
                    print("[EMERGENCY] 💥 CRASH DETECTED BY ESP32! HALTING VEHICLE! 💥")
                    print("!" * 60)
                    self.execute_mission("flashon")
                    self.telemetry.update("crash", True)                    
                    self.stop_autonomous_mode() 
                    break # Break out of the autonomous loop entirely
                # ──────────────────────────────────────────────────────────────

                # ── 2. PARKING HANDLING ───────────────────────────────────────
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

                        # NOTE: The loop freezes here waiting for keyboard input.
                        # Since the car is already commanded to stop ("s") and threads are killed,
                        # this is acceptable, but the crash check won't monitor while waiting.
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
                
                # ── 3. MISSION AND USER COMMANDS ──────────────────────────────
                mission_cmd = self.command_queue.get_mission_command()
                if mission_cmd:
                    self.execute_mission(mission_cmd)
                    print(f"[MISSION] Executed mission command: {mission_cmd}")

                cc = self.get_user_command_non_blocking()
                if cc == "s":
                    self.stop_autonomous_mode()
                    break
                if cc:
                    self.execute_mission(cc)

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
        last_time = time.perf_counter()
        
        while self.autonomous_mode_lane_running:
            try:
                current_time = time.perf_counter()
                delay_ms = (current_time - last_time) * 1000

                if self.red_light_active :
                    last_time = current_time
                    continue

                frame = self.get_current_frame()
                if frame is not None:
                    result= process_lane(frame)
                    print(result[10])
                    # Extract desired steering from mission string
                    try:
                        desired_steer = result[10]
                    except (IndexError, ValueError):
                        desired_steer = 104

                    # Get list of steering values to send (may be 1 or many)
                    steering_values = self.steer_smoother.update(desired_steer)
                    print(steering_values)
                    # Send ALL intermediate values to the car
                    for steer_value in steering_values:
                        smoothed_mission = f"t {steer_value}"
                        self.main_thread_commands.put(smoothed_mission)
                        
                        # Optional: small delay between steps if needed
                        # time.sleep(0.05)  # 50ms between steps

                last_time = current_time

            except Exception as e:
                print(f"[LANE] Error: {e}")
    def detect_loop(self):
        last_time = time.perf_counter()

        while self.autonomous_mode_traffic_running:
            current_time = time.perf_counter()

            try:
                if self.parking_mode_running or self.waiting_for_parking_response:
                    last_time = current_time
                    continue

                if self.red_light_active:
                    self.main_thread_commands.put("s")
                    last_time = current_time
  

                frame = self.get_current_frame()
                if frame is None:
                    last_time = current_time
                    continue

                # ── Run all 3 models ──────────────────────────────────────────
                traffic_decision, traffic_type = self.check_traffic(self.traffic_model.detect(frame))
                speed_decision,   speed_type   = self.check_speed(self.speed_model.detect(frame))
                general_decision, general_type = self.check_general(self.general_model.detect(frame))

                # ── 1. Traffic light / parking / bump ─────────────────────────
                if traffic_type == "red_light":
                    self.telemetry.update("traffic_light", "red")
                    self.red_light_active = True
                    if self.autonomous_mode_lane_running:
                        print("[TRAFFIC] 🛑 Red light - DEACTIVATING lane detection")
                        self.telemetry.update("traffic_light", "red")
                        self.autonomous_mode_lane_running = False
                        self.main_thread_commands.put("s")
                    self.main_thread_commands.put("s")

                elif traffic_type == "green_light":
                    self.telemetry.update("traffic_light", "green")
                    self.red_light_active = False
                    if not self.autonomous_mode_lane_running:
                        print("[TRAFFIC] 🟢 Green light - REACTIVATING lane detection")
                        self.telemetry.update("traffic_light", "green")
                        self.autonomous_mode_lane_running = True
                        self.lane_thread = threading.Thread(
                            target=self.lane_loop, daemon=True, name="LaneThread"
                        )
                        self.lane_thread.start()
                    self.main_thread_commands.put("f 100")

                elif traffic_type in ("yellow_light", "bump_sign"):
                    self.telemetry.update("traffic_light", "yellow")
                    self.main_thread_commands.put(traffic_decision)

                elif traffic_type == "parking_area" and not self.waiting_for_parking_response:
                    self.user_input_queue.put("parking_request")
                else:
                    self.telemetry.update("traffic_light", "none")

                # ── 2. Speed limit ────────────────────────────────────────────
                if speed_decision :
                    self.telemetry.update("speed", speed_decision.split(" ")[1])
                    if not self.red_light_active:
                        self.main_thread_commands.put(speed_decision)

                # ── 3. General (stop for obstacles) ──────────────────────────
                if general_decision:
                    if general_decision == "s":
                        self.telemetry.update("detected_sign", "caution")
                        self.telemetry.update("speed", 0)
                        if self.autonomous_mode_lane_running:
                            self.autonomous_mode_lane_running = False
                        self.main_thread_commands.put(general_decision)
                    elif general_decision == "f" and not self.red_light_active:
                        self.telemetry.update("detected_sign", "none")
                        self.red_light_active = False
                        if not self.autonomous_mode_lane_running:
                            self.autonomous_mode_lane_running = True
                            self.lane_thread = threading.Thread(
                                target=self.lane_loop, daemon=True, name="LaneThread"
                            )
                            self.lane_thread.start()
                            time.sleep(1)  # Small delay to ensure lane thread starts before sending command
                        self.main_thread_commands.put(general_decision)

                last_time = current_time

            except Exception as e:
                print(f"[DETECT] Error: {e}")
                import traceback
                traceback.print_exc()

        return None
