from .mission_commands import MISSION_MAP

class Mission:
    def __init__(self, mission=None):  
        pass
        
    def update(self, new_mission):  
        new_mission = new_mission.lower().strip()  
          
        # Handle speed commands
        if new_mission.startswith("speed="):  
            self.current_mission = new_mission  
            print(f"[MISSION] Updated to '{new_mission}'")  
            return True, new_mission
          
        # Handle turn commands with wheel speeds (e.g., "l 150 50", "r 180 20")
        if new_mission.startswith("t ") :
            parts = new_mission.split()
            if len(parts) == 3:
                try:
                    left_pwm = int(parts[1])
                    right_pwm = int(parts[2])
                    if 0 <= left_pwm <= 255 and 0 <= right_pwm <= 255:
                        self.current_mission = new_mission
                        print(f"[MISSION] Updated to '{new_mission}'")
                        return True, new_mission
                    else:
                        print(f"[MISSION] Invalid PWM values (0-255 only): '{new_mission}'")
                        return False, None
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False, None
            else:
                print(f"[MISSION] Invalid turn command format. Use: 'l 150 50' or 'r 180 20'")
                return False, None
          
        # Validate against MISSION_MAP for single-letter commands
        if new_mission in MISSION_MAP:  
            self.current_mission = new_mission  
            print(f"[MISSION] Updated to '{new_mission}'")  
            return True, new_mission 
          
        print(f"[MISSION] Invalid mission: '{new_mission}'")  
        return False, None

    def execute(self, controller, given_mission):  
        if not given_mission:  
            print("[MISSION] No mission set.")  
            return  
        
        # Handle "speed=xxx" commands  
        if given_mission.startswith("speed="):  
            controller.send_command(given_mission)  
            return  
        
        # Handle turn commands with wheel speeds (e.g., "l 150 50", "r 180 20")
        if given_mission.startswith("t "):
            parts = given_mission.split()
            if len(parts) == 3:
                try:
                    left_pwm = int(parts[1])
                    right_pwm = int(parts[2])
                    if 0 <= left_pwm <= 255 and 0 <= right_pwm <= 255:
                        print(f"[MISSION] Executing '{given_mission}'")
                        controller.send_command(given_mission)
                        return
                    else:
                        print(f"[MISSION] Invalid PWM values (0-255 only): '{given_mission}'")
                        return
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{given_mission}'")
                    return
            else:
                print(f"[MISSION] Invalid turn command format: '{given_mission}'")
                return
        
        # Use MISSION_MAP for single-letter commands  
        mission = given_mission  
        if mission in MISSION_MAP:  
            print(f"[MISSION] Executing '{mission}'")  
            MISSION_MAP[mission](controller)  
        else:  
            print(f"[MISSION] Unknown mission: '{mission}'")