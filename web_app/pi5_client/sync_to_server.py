#!/usr/bin/env python3
"""
Sync Script - Watches telemetry file and uploads to server
"""

import requests
import json
import time
import sys
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def load_config():
    """Load configuration"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found!")
        sys.exit(1)

class TelemetryUploader(FileSystemEventHandler):
    """Watches telemetry file and uploads changes to server"""
    
    def __init__(self, server_url, data_file, debug=True):
        self.server_url = server_url
        self.data_file = os.path.abspath(data_file)  # Use absolute path for reliable matching
        self.debug = debug
        self.last_upload = 0
        self.upload_count = 0
        self.error_count = 0
        
    def process_event(self, event_path):
        """Core check and upload trigger with a small debounce filter"""
        if os.path.basename(event_path) == os.path.basename(self.data_file):
            current_time = time.time()
            # 0.15 second debounce allows rapid steering changes while preventing double-fires
            if current_time - self.last_upload < 0.15:
                return
            
            self.upload_data()
            self.last_upload = current_time

    def on_modified(self, event):
        """Fires if the file is modified in place"""
        self.process_event(event.src_path)
        
    def on_created(self, event):
        """Fires if the file is created fresh"""
        self.process_event(event.src_path)

    def on_moved(self, event):
        """Fires when tmp.replace() swaps the file over the destination target"""
        if hasattr(event, 'dest_path'):
            self.process_event(event.dest_path)
        else:
            self.process_event(event.src_path)
    
    def upload_data(self):
        """Upload telemetry data to server"""
        try:
            # Read file
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Send to server
            response = requests.post(
                f"{self.server_url}/api/telemetry",
                json=data,
                timeout=2
            )
            
            if response.status_code == 200:
                self.upload_count += 1
                
                if self.debug:
                    
                    print(f"✓ [{self.upload_count:04d}] Uploaded! | Mode: {mode_val} | "
                          f"Steering: {steering_val}° | Servo: {servo_val}° | Speed: {data['speed']:.1f}")
            else:
                self.error_count += 1
                print(f"✗ Upload failed: HTTP {response.status_code}")
                try:
                    print(f"  Server response: {response.text}")
                except:
                    pass
                
        except FileNotFoundError:
            pass  # Small race condition mitigation if file is briefly missing during copy swap
        except requests.exceptions.ConnectionError:
            self.error_count += 1
            print(f"✗ Cannot connect to server: {self.server_url}")
        except requests.exceptions.Timeout:
            self.error_count += 1
            print(f"✗ Request timeout")
        except requests.exceptions.RequestException as e:
            self.error_count += 1
            print(f"✗ Network error: {e}")
        except json.JSONDecodeError:
            pass  # Avoid crashing if we catch the file half-written
        except Exception as e:
            self.error_count += 1
            print(f"✗ Error: {e}")

def main():
    """Main function"""
    config = load_config()
    
    server_url = config['server_url']
    data_file = os.path.abspath(config['data_file'])
    debug = config.get('debug', True)
    
    print("=" * 60)
    print("🔄 Telemetry Sync Script (Atomic-Safe Edition)")
    print("=" * 60)
    print(f"📡 Server: {server_url}")
    print(f"📁 Watching: {data_file}")
    print(f"🚗 Car ID: {config['car_id']}")
    print("=" * 60)
    print("\n⏳ Watching for telemetry data updates...\n")
    
    # Test server connection
    try:
        response = requests.get(f"{server_url}/", timeout=2)
        print(f"✓ Server is reachable!\n")
    except:
        print(f"⚠️  WARNING: Cannot reach server at {server_url}")
        print(f"   Make sure the Flask server is running on your laptop!")
        print(f"   Press Ctrl+C to stop, or wait for server to start...\n")
    
    # Create uploader
    uploader = TelemetryUploader(server_url, data_file, debug)
    
    # Watch the directory containing the telemetry file
    watch_dir = os.path.dirname(data_file) or '.'
    observer = Observer()
    observer.schedule(uploader, path=watch_dir, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n" + "=" * 60)
        print("🛑 Sync stopped")
        print(f"📊 Stats: {uploader.upload_count} uploads, {uploader.error_count} errors")
        print("=" * 60)
    
    observer.join()

if __name__ == "__main__":
    main()