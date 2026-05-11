from .mission_commands import MISSION_MAP

class Mission:
    def __init__(self, mission=None):  
        pass
        
    def execute(self, controller, new_mission):
        """Update and execute mission in one function"""
        if not new_mission:
            print("[MISSION] No mission provided.")
            return False
            
        new_mission = new_mission.lower().strip()
        
        if len(new_mission) == 0:
            return False
        
        # === HANDLE GLOBAL SPEED SET ===
        if new_mission.startswith("speed="):
            try:
                new_speed = int(new_mission.split("=")[1])
                if 0 <= new_speed <= 255:
                    self.global_speed = new_speed
                    print(f"[MISSION] Global speed set to {new_speed}")
                    return True
                else:
                    print(f"[MISSION] Invalid speed value (0-255 only): '{new_mission}'")
                    return False
            except ValueError:
                print(f"[MISSION] Invalid number format: '{new_mission}'")
                return False
        
        parts = new_mission.split()
        cmd = parts[0]
        
        # === FORWARD ===
        if cmd == "f":
            if len(parts) == 2:
                try:
                    speed = int(parts[1])
                    if 0 <= speed <= 255:
                        self.current_mission = new_mission
                        controller.send_command(new_mission)
                        return True
                    else:
                        print(f"[MISSION] Invalid speed value (0-255 only): '{new_mission}'")
                        return False
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False
            elif len(parts) == 1:
                speed = getattr(self, "global_speed", 150)
                mission_cmd = f"f {speed}"
                self.current_mission = mission_cmd
                controller.send_command(mission_cmd)
                return True
            else:
                print(f"[MISSION] Invalid forward command format. Use: 'f' or 'f 200'")
                return False
        
        # === BACKWARD ===
        if cmd == "b":
            if len(parts) == 2:
                try:
                    speed = int(parts[1])
                    if 0 <= speed <= 255:
                        self.current_mission = new_mission
                        controller.send_command(new_mission)
                        return True
                    else:
                        print(f"[MISSION] Invalid speed value (0-255 only): '{new_mission}'")
                        return False
                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False
            elif len(parts) == 1:
                speed = getattr(self, "global_speed", 150)
                mission_cmd = f"b {speed}"
                self.current_mission = mission_cmd
                controller.send_command(mission_cmd)
                return True
            else:
                print(f"[MISSION] Invalid backward command format. Use: 'b' or 'b 200'")
                return False
        
        # === TURN ===
        if cmd == "t":
            if len(parts) == 2:
                try:
                    servo_angle = int(parts[1])

                    if 50 <= servo_angle <= 140:
                        self.current_mission = new_mission
                        controller.send_command(new_mission)
                        return True
                    else:
                        print(f"[MISSION] Servo angle out of range (50-140): '{new_mission}'")
                        return False

                except ValueError:
                    print(f"[MISSION] Invalid number format: '{new_mission}'")
                    return False
            else:
                print(f"[MISSION] Invalid format. Use: 't 90'")
                return False
        # === STOP ===
        if cmd == "s":
            if len(parts) == 1:
                self.current_mission = new_mission
                controller.send_command(new_mission)
                return True
            else:
                print(f"[MISSION] Invalid stop command format. Use: 's'")
                return False

        # === PARK ===
        if cmd == "park":
            if len(parts) == 1:
                self.current_mission = new_mission
                print("[MISSION] Parking initiated!")
                controller.send_command(new_mission)
                return True
            else:
                print(f"[MISSION] Invalid park command format. Use: 'park'")
                return False
        
        print(f"[MISSION] Invalid mission: '{new_mission}'")
        return False