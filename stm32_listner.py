#!/usr/bin/env python3
import serial
import serial.tools.list_ports
import time
import sys

def find_stm32_port():
    """Find the STM32 serial port automatically"""
    print("🔍 Searching for STM32...")
    
    # Common STM32 USB identifiers
    stm32_identifiers = ['STM', 'CH340', 'CP2102', 'FTDI', '0483:', '1a86:', '10c4:']
    
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"  📍 Found: {port.device} - {port.description}")
        
        # Check if it's likely an STM32 or serial device
        if any(id in f"{port.description} {port.hwid}" for id in stm32_identifiers):
            print(f"✅ STM32/serial device detected on {port.device}")
            return port.device
    
    # If auto-detection fails, show available ports
    print("\n📋 Available serial ports:")
    for port in ports:
        print(f"  {port.device} - {port.description}")
    
    return None

def main():
    # Auto-detect STM32
    port = find_stm32_port()
    
    if not port:
        port = input("🚨 Enter the port manually (e.g., /dev/ttyUSB0, /dev/ttyACM0, /dev/ttyAMA0): ").strip()
    
    if not port:
        print("❌ No port specified. Exiting.")
        return
    
    try:
        print(f"\n🔌 Connecting to {port} at 115200 baud...")
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=1
        )
        
        print("✅ Connected successfully!")
        print("📡 Listening for STM32 messages...")
        print("⏹️  Press Ctrl+C to stop\n")
        print("-" * 50)
        
        message_count = 0
        
        while True:
            try:
                # Read data from STM32
                if ser.in_waiting > 0:
                    data = ser.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        message_count += 1
                        timestamp = time.strftime("%H:%M:%S")
                        print(f"🕒 [{timestamp}] #{message_count:03d} → {data}")
                
                time.sleep(0.1)  # Small delay to reduce CPU usage
                
            except KeyboardInterrupt:
                print(f"\n\n📊 Received {message_count} messages total")
                print("👋 Goodbye!")
                break
            except UnicodeDecodeError:
                # Handle any encoding issues
                continue
                
    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if STM32 is powered (LED should be on)")
        print("2. Try a different USB cable")
        print("3. Check if port is correct")
        print("4. Make sure STM32 code is running")
        print("5. Check baud rate matches (115200)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("🔌 Serial port closed")

if __name__ == "__main__":
    main()