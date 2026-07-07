import serial

class ESP32Sensor:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        
        try:
            # timeout=0 ensures the readline() is completely non-blocking
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0)
            print(f"[INFO] ESP32 initialized on {self.port}")
        except Exception as e:
            print(f"[WARNING] Could not connect to ESP32: {e}")

    def is_crash_detected(self):
            """
            Checks the serial buffer for 'CRASH'.
            Clears the buffer immediately if found to prevent ghost triggers.
            """
            if self.ser and self.ser.in_waiting > 0:
                try:
                    # Read all lines currently waiting in the buffer
                    while self.ser.in_waiting > 0:
                        msg = self.ser.readline().decode('utf-8', errors='ignore').strip()
                        
                        if msg == "CRASH":
                            # ── THE MAGIC LINE ────────────────────────────────────
                            # Clear everything out of the Pi's serial receive buffer
                            self.ser.reset_input_buffer() 
                            # ──────────────────────────────────────────────────────
                            return True
                except Exception as e:
                    print(f"[ERROR] Failed to read from ESP32: {e}")
                    
            return False

    def close(self):
        """Clean up the serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[INFO] ESP32 connection closed.")