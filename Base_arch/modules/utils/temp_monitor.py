class Temp_monitor:
    def __init__(self):
        pass

    def get_temp(self):
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0
        return temp