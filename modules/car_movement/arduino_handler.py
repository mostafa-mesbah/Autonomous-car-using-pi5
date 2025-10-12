import time
import sys
import serial
class ArduinoCarController:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        self.port=port
        self.baudrate=baudrate
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            print(f"Connected to Arduino on {self.port}")
            self.read_arduino_message()
        except Exception as e:
            print(f"Error connecting to Arduino: {e}")
            sys.exit(1)
    
    def read_arduino_message(self):
        """Read and print initial message from Arduino"""
        if self.ser.in_waiting > 0:
            message = self.ser.readline().decode().strip()
            print(f"Arduino: {message}")
    
    def send_command(self, command, duration=None):
        """Send command to Arduino"""
        commands = {'F': 'FORWARD', 'B': 'BACKWARD', 'R': 'RIGHT', 
                   'L': 'LEFT', 'S': 'STOP'}
        
        if command in commands:
            print(f"Sending command: {commands[command]}")
            self.ser.write(command.encode())
            
            # Read Arduino response
            time.sleep(0.1)
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode().strip()
                print(f"Arduino: {response}")
            
            # If duration specified, stop after that time
            if duration and command != 'S':
                time.sleep(duration)
                self.send_command('S')
        else:
            print(f"Unknown command: {command}")
    
    def forward(self, duration=None):
        self.send_command('F', duration)
    
    def backward(self, duration=None):
        self.send_command('B', duration)
    
    def right(self, duration=None):
        self.send_command('R', duration)
    
    def left(self, duration=None):
        self.send_command('L', duration)
    
    def stop(self):
        self.send_command('S')
    
    def close(self):
        self.ser.close()
        print("Connection closed")
