from .mission_commands import MISSION_MAP

class Mission:
    def __init__(self, mission=None):  
        pass
        
    def update(self, new_mission):
        new_mission = new_mission.lower().strip()
        
        if len(new_mission) == 0:
            return False, None
        
        parts = new_mission.split()
        cmd = parts[0]
        
        # === FORWARD ===
        if cmd == "f":
            if len(parts) == 2:
                try:
                    speed = int(parts[1])
                    if 0 <= speed <= 255:
                        self.current_mission = new_mission
                        return True, new_mission
                    else:
                        print(f"[MISSION] Invalid speed value (0-255 only): '{new_mission}'")
                        return False, None
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False, None
            elif len(parts) == 1:
                self.current_mission = new_mission
                return True, new_mission
            else:
                print(f"[MISSION] Invalid forward command format. Use: 'f' or 'f 200'")
                return False, None
        
        # === BACKWARD ===
        if cmd == "b":
            if len(parts) == 2:
                try:
                    speed = int(parts[1])
                    if 0 <= speed <= 255:
                        self.current_mission = new_mission
                        return True, new_mission
                    else:
                        print(f"[MISSION] Invalid speed value (0-255 only): '{new_mission}'")
                        return False, None
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False, None
            elif len(parts) == 1:
                self.current_mission = new_mission
                return True, new_mission
            else:
                print(f"[MISSION] Invalid backward command format. Use: 'b' or 'b 200'")
                return False, None
        
        # === ROLL LEFT ===
        if cmd == "rl":
            if len(parts) == 2:
                try:
                    speed = int(parts[1])
                    if 0 <= speed <= 255:
                        self.current_mission = new_mission
                        return True, new_mission
                    else:
                        print(f"[MISSION] Invalid speed value (0-255 only): '{new_mission}'")
                        return False, None
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False, None
            elif len(parts) == 1:
                self.current_mission = new_mission
                return True, new_mission
            else:
                print(f"[MISSION] Invalid roll left command format. Use: 'rl' or 'rl 200'")
                return False, None
        
        # === ROLL RIGHT ===
        if cmd == "rr":
            if len(parts) == 2:
                try:
                    speed = int(parts[1])
                    if 0 <= speed <= 255:
                        self.current_mission = new_mission
                        return True, new_mission
                    else:
                        print(f"[MISSION] Invalid speed value (0-255 only): '{new_mission}'")
                        return False, None
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False, None
            elif len(parts) == 1:
                self.current_mission = new_mission
                return True, new_mission
            else:
                print(f"[MISSION] Invalid roll right command format. Use: 'rr' or 'rr 200'")
                return False, None
        
        # === TURN ===
        if cmd == "t":
            if len(parts) == 3:
                try:
                    left_speed = int(parts[1])
                    right_speed = int(parts[2])
                    if 0 <= left_speed <= 255 and 0 <= right_speed <= 255:
                        self.current_mission = new_mission
                        return True, new_mission
                    else:
                        print(f"[MISSION] Invalid speed values (0-255 only): '{new_mission}'")
                        return False, None
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False, None
            else:
                print(f"[MISSION] Invalid turn command format. Use: 't 150 50'")
                return False, None
        
        # === STOP ===
        if cmd == "s":
            if len(parts) == 1:
                self.current_mission = new_mission
                return True, new_mission
            else:
                print(f"[MISSION] Invalid stop command format. Use: 's'")
                return False, None
        
        print(f"[MISSION] Invalid mission: '{new_mission}'")
        return False, None

    def execute(self, controller, given_mission):  
        if not given_mission:  
            print("[MISSION] No mission set.")  
            return  
        else:
            controller.send_command(given_mission)
            return True