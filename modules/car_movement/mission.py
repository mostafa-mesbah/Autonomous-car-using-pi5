from .mission_commands import MISSION_MAP

class Mission:
    def __init__(self, mission=None):
        self.current_mission = mission

    def update(self, new_mission):
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
        action = MISSION_MAP.get(self.current_mission)
        print(f"[MISSION] Executing '{self.current_mission}'")
        action(controller)
