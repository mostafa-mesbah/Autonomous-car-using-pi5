import serial

# Change if needed
PORT = "/dev/ttyUSB0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

print("Listening to ESP32...")

while True:
    if ser.in_waiting:
        data = ser.readline().decode().strip()
        print("Received:", data)
