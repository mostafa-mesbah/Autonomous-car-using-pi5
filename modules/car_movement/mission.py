from .mission_commands import MISSION_MAP

class Mission:
    def __init__(self, mission=None):  
        pass
        
    def update(self, new_mission):
        new_mission = new_mission.lower().strip()
        
        if len(new_mission) == 0:
            return False, None
        
        # === HANDLE GLOBAL SPEED SET ===
        if new_mission.startswith("speed="):
            try:
                new_speed = int(new_mission.split("=")[1])
                if 0 <= new_speed <= 255:
                    self.global_speed = new_speed
                    print(f"[MISSION] Global speed set to {new_speed}")
                    return True, new_mission
                else:
                    print(f"[MISSION] Invalid speed value (0-255 only): '{new_mission}'")
                    return False, None
            except ValueError:
                print(f"[MISSION] Invalid number format: '{new_mission}'")
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
                speed = getattr(self, "global_speed", 150)
                self.current_mission = f"f {speed}"
                return True, self.current_mission
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
                speed = getattr(self, "global_speed", 150)
                self.current_mission = f"b {speed}"
                return True, self.current_mission
            else:
                print(f"[MISSION] Invalid backward command format. Use: 'b' or 'b 200'")
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

        # === PARK ===
        if cmd == "park":
            if len(parts) == 1:
                # Add any special behavior for parking here
                self.current_mission = new_mission
                print("[MISSION] Parking initiated!")
                return True, new_mission
            else:
                print(f"[MISSION] Invalid park command format. Use: 'park'")
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