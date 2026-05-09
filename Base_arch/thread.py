#!/usr/bin/env python3
import os
import time
import subprocess
import sys

def find_car_pid():
    """Find the autonomous car process PID"""
    try:
        result = subprocess.run(['pgrep', '-f', 'python3 main.py'], 
                              capture_output=True, text=True)
        if result.stdout:
            return int(result.stdout.strip().split('\n')[0])
    except:
        pass
    return None

def monitor_threads(pid):
    """Monitor threads with names"""
    while True:
        os.system('clear')
        print(f"Monitoring threads for PID: {pid}")
        print("=" * 80)
        print(f"{'TID':>8} {'CPU%':>6} {'Name':<25} {'Time'}")
        print("-" * 80)
        
        try:
            # Check if process still exists
            if not os.path.exists(f'/proc/{pid}'):
                print(f"\nProcess {pid} no longer running!")
                break
            
            # Get thread list
            for tid in os.listdir(f'/proc/{pid}/task/'):
                try:
                    # Get thread name
                    with open(f'/proc/{pid}/task/{tid}/comm', 'r') as f:
                        name = f.read().strip()
                    
                    # Get thread stats
                    with open(f'/proc/{pid}/task/{tid}/stat', 'r') as f:
                        stats = f.read().split()
                    
                    # CPU usage (simplified)
                    utime = int(stats[13])
                    stime = int(stats[14])
                    total_time = utime + stime
                    
                    print(f"{tid:>8} {total_time:>6} {name:<25}")
                    
                except Exception as e:
                    pass
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pid = int(sys.argv[1])
    else:
        pid = find_car_pid()
        if not pid:
            print("Could not find car process. Make sure your car is running.")
            print("Usage: python thread_monitor.py [PID]")
            sys.exit(1)
    
    monitor_threads(pid)