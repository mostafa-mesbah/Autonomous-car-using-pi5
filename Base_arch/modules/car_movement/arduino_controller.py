import time
import serial
import sys

class ArduinoCarController:

    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        """Initialize serial connection to Arduino."""
        self.port = port
        self.baudrate = baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Allow Arduino to reset after connection
            print(f"[info] connected to arduino on {self.port}")
        except Exception as e:
            print(f"[error] failed to connect to arduino: {e}")
            sys.exit(1)

    def send_command(self, command):
        self.ser.write(f"{command}\n".encode())
                  
    # === Movement wrappers ===
    def forward(self): self.send_command('f')
    def backward(self): self.send_command('b')
    def stop(self): self.send_command('s')
    def roll_left(self): self.send_command('rl')
    def roll_right(self): self.send_command('rr')
    def close(self):
        self.ser.close()
        print("[info] connection closed")