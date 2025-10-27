import time
import serial
import sys

class ArduinoCarController:
    """
    Controller for communicating with the Arduino-based car over serial.
    Supports movement commands, speed control, and GPS mode toggling.
    """

    COMMANDS = {
        'f': 'move forward',
        'b': 'move backward',
        's': 'stop',
        'l': 'turn left',
        'r': 'turn right',
        'rl': 'roll left',
        'rr': 'roll right',
        'g': 'toggle gps mode'
    }

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
        """Send a command to Arduino and read its response."""
        if not command:
            return

        # Handle speed command (e.g., "speed=180")
        if command.startswith("speed="):
            print(f"[send] setting speed -> {command}")
            self.ser.write(f"{command}\n".encode())

        # Handle movement and gps commands
        elif command in self.COMMANDS:
            print(f"[send] {self.COMMANDS[command]}")
            self.ser.write(f"{command}\n".encode())

        else:
            print(f"[warn] unknown command: {command}")
            return

        # Read response (if available)
        time.sleep(0.1)
        if self.ser.in_waiting:
            try:
                response = self.ser.read(self.ser.in_waiting).decode(errors='ignore').strip()
                if response:
                    print(f"[arduino] {response}")
            except Exception as e:
                print(f"[warn] failed to read response: {e}")

    # === Movement wrappers ===
    def forward(self): self.send_command('f')
    def backward(self): self.send_command('b')
    def stop(self): self.send_command('s')
    def turn_left(self): self.send_command('l')
    def turn_right(self): self.send_command('r')
    def roll_left(self): self.send_command('rl')
    def roll_right(self): self.send_command('rr')
    def toggle_gps(self): self.send_command('g')

    # === Speed control ===
    def set_speed(self, value): self.send_command(f"speed={value}")

    # === Close connection ===
    def close(self):
        self.ser.close()
        print("[info] connection closed")
