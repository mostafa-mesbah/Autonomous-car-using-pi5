#!/usr/bin/env python3
import json
import time
import os
import sys

# Update this path to match your log file location
LOG_FILE = "/home/mostafa/old_version/Autonomous-car-using-pi5/Base_arch/car_state.json"

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def format_value(key, value):
    """Format different value types nicely"""
    if isinstance(value, float):
        return f"{value:8.2f}"
    elif isinstance(value, int):
        return f"{value:8d}"
    else:
        return f"{value:15s}" if isinstance(value, str) else f"{value}"

def monitor(refresh_rate=0.2):
    """Monitor and display car state in real-time"""
    
    print(f"Monitoring: {LOG_FILE}")
    print("Press Ctrl+C to exit")
    print("=" * 60)
    
    last_state = {}
    
    while True:
        try:
            # Read the latest state
            with open(LOG_FILE, 'r') as f:
                state = json.load(f)
            
            # Clear screen only if state changed
            if state != last_state:
                clear_screen()
                
                # Print header
                print("=" * 60)
                print("CAR STATE MONITOR".center(60))
                print("=" * 60)
                print(f"Updated: {time.strftime('%H:%M:%S')}")
                print("-" * 60)
                
                # Print all variables
                if state:
                    # Group by category (optional - based on key names)
                    categories = {
                        "Status": ["status", "autonomous_mode", "current_mission", "car_speed"],
                        "Delays": ["cmd_delay_ms", "lane_delay_ms", "detect_delay_ms", "capture_delay_ms"],
                        "Other": []
                    }
                    
                    # Sort and display
                    for category, keys in categories.items():
                        printed = False
                        for key in keys:
                            if key in state:
                                if not printed:
                                    print(f"\n{category}:")
                                    printed = True
                                value = state[key]
                                print(f"  {key:20s}: {format_value(key, value)}")
                    
                    # Display remaining keys
                    printed_other = False
                    for key, value in sorted(state.items()):
                        # Skip keys already displayed
                        if key in categories["Status"] or key in categories["Delays"]:
                            continue
                        if not printed_other:
                            print("\nOther:")
                            printed_other = True
                        print(f"  {key:20s}: {format_value(key, value)}")
                else:
                    print("Waiting for data...")
                
                print("\n" + "=" * 60)
                last_state = state.copy()
            
            time.sleep(refresh_rate)
            
        except FileNotFoundError:
            clear_screen()
            print("=" * 60)
            print("CAR STATE MONITOR".center(60))
            print("=" * 60)
            print(f"\nWaiting for car logger to start...")
            print(f"File not found: {LOG_FILE}")
            print("\nMake sure your car script is running.")
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
            break
        except json.JSONDecodeError:
            print(f"Error reading JSON file. File may be corrupted.")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    monitor()