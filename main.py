
from modules.car_movement.autonomous_car import Autonomous_Car
def main():
    car=Autonomous_Car(50,100)

    while True:
        mission_input = input("Enter something or (stop): ")
        
        print(f"You entered: {mission_input}")
        if mission_input.lower() == 'stop':
            print("Goodbye!")
            break
        else:
            if car.update_mission(mission_input) :
                car.execute_mission()
            else:
                print("could not update mission")
                print("stoping the car")

if __name__ == "__main__":
    main()