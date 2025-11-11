from .mission_commands import MISSION_MAP

class Mission:
    def __init__(self, mission=None):  
        pass
        
    def update(self, new_mission):  
        new_mission = new_mission.lower().strip()  
          
        if new_mission.startswith("t ") :
            parts = new_mission.split()
            if len(parts) == 3:
                try:
                    left_pwm = int(parts[1])
                    right_pwm = int(parts[2])
                    if 0 <= left_pwm <= 255 and 0 <= right_pwm <= 255:
                        self.current_mission = new_mission
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
        if new_mission.startswith("f "):  
            parts = new_mission.split()
            if len(parts) == 2:
                try:
                    speed = int(parts[1])
                    if 0 <= speed <= 255:
                        self.current_mission = new_mission
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
            return True, new_mission 
          
        print(f"[MISSION] Invalid mission: '{new_mission}'")  
        return False, None

    def execute(self, controller, given_mission):  
        if not given_mission:  
            print("[MISSION] No mission set.")  
            return  
        else:
            controller.send_command(given_mission)
            return True