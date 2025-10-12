class Mission:
    def __init__(self,mission = None):
        self.curent_mission = mission
        self.valid_missions = ("move_forward","move_backward","turn_left","turn_right")

    def update_mission(self,new_missoin)-> bool:
        if new_missoin in self.valid_missions:
            self.curent_mission = new_missoin
            print("mission updated")
            return True
        else:
            print("invalid_mission")
            return False
    def excute_mission(self):
        print("executing mission")