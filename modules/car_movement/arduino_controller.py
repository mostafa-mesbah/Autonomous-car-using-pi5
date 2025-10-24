import time
import serial
import sys

class ArduinoCarController:
    COMMANDS = {
        'F': 'FORWARD',
        'B': 'BACKWARD',
        'L': 'LEFT',
        'R': 'RIGHT',
        'S': 'STOP',
        '+': 'INCREASE_SPEED',
        '-': 'DECREASE_SPEED'
    }

    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)
            print(f"[INFO] Connected to Arduino on {self.port}")
        except Exception as e:
            print(f"[ERROR] Failed to connect to Arduino: {e}")
            sys.exit(1)

    def send_command(self, command):
        # Accept direct "speed=xxx" command or single-letter mission
        if not command:
            return


        # Handle speed command
        if command.lower().startswith("speed="):
            print(f"[SEND] Setting speed -> {command}")
            self.ser.write(f"{command}\n".encode())
            return

        # Handle normal mission commands
        if command in self.COMMANDS:
            print(f"[SEND] {self.COMMANDS[command]}")
            self.ser.write(f"{command}\n".encode())
        else:
            print(f"[WARN] Unknown command: {command}")
            return

        time.sleep(0.1)
        if self.ser.in_waiting:
            try:
                response = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
                if response:
                    print(f"[ARDUINO] {response}")
            except Exception as e:
                print(f"[WARN] Failed to read response: {e}")

    def forward(self): self.send_command('F')
    def backward(self): self.send_command('B')
    def left(self): self.send_command('L')
    def right(self): self.send_command('R')
    def stop(self): self.send_command('S')
    def increase_speed(self): self.send_command('+')
    def decrease_speed(self): self.send_command('-')
    def close(self):
        self.ser.close()
        print("[INFO] Connection closed")
