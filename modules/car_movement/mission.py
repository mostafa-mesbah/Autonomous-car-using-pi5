class Mission:
    def __init__(self,mission = None):
        self.current_mission = mission
        self.valid_missions = ("move_forward","move_backward","turn_left","turn_right")

    def update_mission(self,new_missoin)-> bool:
        if new_missoin in self.valid_missions:
            self.current_mission = new_missoin
            print("mission updated")
            return True
        else:
            print("invalid_mission")
            return False
        
    def execute_mission(self, car_controller):
        print(f"executing mission: {self.current_mission}")
        
        if self.current_mission == "move_forward":
            car_controller.forward()
        elif self.current_mission == "move_backward":
            car_controller.backward()
        elif self.current_mission == "turn_left":
            car_controller.left()
        elif self.current_mission == "turn_right":
            car_controller.right()
        else:
            print(f"No action defined for mission: {self.current_mission}")
            print("car will stop")
            car_controller.stop()
        
        