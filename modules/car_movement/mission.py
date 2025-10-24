from .mission_commands import MISSION_MAP

class Mission:
    def __init__(self, mission=None):  
        self.current_mission = mission  
  
    def update(self, new_mission):  
        new_mission = new_mission.lower().strip()  
          
        if new_mission.startswith("speed="):  
            self.current_mission = new_mission  
            print(f"[MISSION] Updated to '{new_mission}'")  
            return True  
          
        # Validate against MISSION_MAP instead  
        if new_mission in MISSION_MAP:  
            self.current_mission = new_mission  
            print(f"[MISSION] Updated to '{new_mission}'")  
            return True  
          
        print(f"[MISSION] Invalid mission: '{new_mission}'")  
        return False
    def execute(self, controller):  
        if not self.current_mission:  
            print("[MISSION] No mission set.")  
            return  
        
        # Handle "speed=xxx" commands  
        if self.current_mission.startswith("speed="):  
            controller.send_command(self.current_mission)  
            return  
        
        # Use MISSION_MAP for single-letter commands  
        mission = self.current_mission  
        if mission in MISSION_MAP:  
            print(f"[MISSION] Executing '{mission}'")  
            MISSION_MAP[mission](controller)  
        else:  
            print(f"[MISSION] Unknown mission: '{mission}'")