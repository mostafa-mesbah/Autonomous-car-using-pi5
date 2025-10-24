class Mission:
    VALID_MISSIONS = {'f', 'b', 'l', 'r', 's', '+', '-'}

    def __init__(self, mission=None):
        self.current_mission = mission

    def update(self, new_mission):
        new_mission = new_mission.lower().strip()
        
        # Accept "speed=xxx" commands
        if new_mission.startswith("speed="):
            self.current_mission = new_mission
            print(f"[MISSION] Updated to '{new_mission}'")
            return True
        
        # Accept single-letter missions
        if new_mission in self.VALID_MISSIONS:
            self.current_mission = new_mission
            print(f"[MISSION] Updated to '{new_mission}'")
            return True
        
        print(f"[MISSION] Invalid mission: '{new_mission}'")
        return False

    def execute(self, controller):
        if not self.current_mission:
            print("[MISSION] No mission set.")
            return

        print(f"[MISSION] Executing '{self.current_mission}'")

        # Handle "speed=xxx"
        if self.current_mission.startswith("speed="):
            controller.send_command(self.current_mission)
            return

        # Handle normal mission letters
        mission = self.current_mission
        if mission == 'f':
            controller.forward()
        elif mission == 'b':
            controller.backward()
        elif mission == 'l':
            controller.left()
        elif mission == 'r':
            controller.right()
        elif mission == 's':
            controller.stop()
        elif mission == '+':
            controller.increase_speed()
        elif mission == '-':
            controller.decrease_speed()
