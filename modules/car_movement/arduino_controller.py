import time
import serial
import sys

class ArduinoCarController:
    COMMANDS = {
        'f': 'FORWARD',
        'b': 'BACKWARD',
        'l': 'LEFT',
        'r': 'RIGHT',
        's': 'STOP',
        '+': 'INCREASE_SPEED',
        '-': 'DECREASE_SPEED'
    }

    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            print(f"[INFO] Connected to Arduino on {self.port}")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Arduino: {e}")
            sys.exit(1)

    def send_command(self, command, duration=None):
        if command not in self.COMMANDS:
            print(f"[WARN] Unknown command: {command}")
            return

        print(f"[SEND] {self.COMMANDS[command]}")
        self.ser.write(command.encode())

        time.sleep(0.1)
        if self.ser.in_waiting:
            response = self.ser.readline().decode().strip()
            print(f"[ARDUINO] {response}")

        if duration and command != 's':
            time.sleep(duration)
            self.send_command('s')

    def forward(self, duration=None): self.send_command('f', duration)
    def backward(self, duration=None): self.send_command('b', duration)
    def left(self, duration=None): self.send_command('l', duration)
    def right(self, duration=None): self.send_command('r', duration)
    def stop(self): self.send_command('s')
    def increase_speed(self): self.send_command('+')
    def decrease_speed(self): self.send_command('-')

    def close(self):
        self.ser.close()
        print("[INFO] Connection closed")
