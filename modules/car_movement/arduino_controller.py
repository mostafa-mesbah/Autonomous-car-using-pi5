import time
import serial
import sys

class ArduinoCarController:
    """
    Controller for communicating with the Arduino-based car over serial.
    Supports movement commands, speed control, GPS mode toggling, and wheel-specific speeds.
    """

    COMMANDS = {
        'f': 'move forward',
        'b': 'move backward',
        's': 'stop',
        'l': 'turn left (default)',
        'r': 'turn right (default)',
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

        # Handle turn commands with wheel speeds (e.g., "l 150 50", "r 180 20")
        if command.startswith("t ") :
            parts = command.split()
            if len(parts) == 3:
                try:
                    left_pwm = int(parts[1])
                    right_pwm = int(parts[2])
                    if 0 <= left_pwm <= 255 and 0 <= right_pwm <= 255:
                        direction = "left" if command.startswith("l ") else "right"
                        print(f"[send] turn {direction} -> L:{left_pwm} R:{right_pwm}")
                        self.ser.write(f"{command}\n".encode())
                    else:
                        print(f"[warn] PWM values must be 0-255: {command}")
                except ValueError:
                    print(f"[warn] invalid PWM values: {command}")
            else:
                print(f"[warn] invalid turn command format: {command}")

        # Handle both wheels speed command (e.g., "both=180", "speed=150")
        elif command.startswith("both=") or command.startswith("speed="):
            try:
                value = int(command.split('=')[1])
                if 0 <= value <= 255:
                    cmd_type = "both" if command.startswith("both=") else "speed"
                    print(f"[send] set {cmd_type} wheels speed -> {value}")
                    self.ser.write(f"{command}\n".encode())
                else:
                    print(f"[warn] speed must be 0-255: {command}")
            except ValueError:
                print(f"[warn] invalid speed value: {command}")

        # Handle basic movement and gps commands
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
    def set_speed(self, value): self.send_command(f"both={value}")
    
    # === Turn with specific wheel speeds ===
    def turn_left_with_speeds(self, left_pwm, right_pwm): 
        self.send_command(f"l {left_pwm} {right_pwm}")
    
    def turn_right_with_speeds(self, left_pwm, right_pwm): 
        self.send_command(f"r {left_pwm} {right_pwm}")

    # === Close connection ===
    def close(self):
        self.ser.close()
        print("[info] connection closed")