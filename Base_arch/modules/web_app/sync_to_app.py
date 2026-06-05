"""
TelemetrySyncClient - Independent Class
Watches a local telemetry JSON file and uploads updates to an online server.
"""

import requests
import json
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TelemetryUploaderHandler(FileSystemEventHandler):
    """Internal Watchdog Handler that watches the specific file path"""
    def __init__(self, server_url, data_file, debug=True):
        self.server_url = server_url
        self.data_file = os.path.abspath(data_file)
        self.debug = debug
        self.last_upload = 0
        self.upload_count = 0
        self.error_count = 0
        
    def process_event(self, event_path):
        if os.path.abspath(event_path) == self.data_file:
            current_time = time.time()
            # 0.15 second debounce allows rapid steering changes while preventing double-fires
            if current_time - self.last_upload < 0.15:
                return
            
            self.upload_data()
            self.last_upload = current_time

    def on_modified(self, event):
        self.process_event(event.src_path)
        
    def on_created(self, event):
        self.process_event(event.src_path)

    def on_moved(self, event):
        if hasattr(event, 'dest_path'):
            self.process_event(event.dest_path)
        else:
            self.process_event(event.src_path)
    
    def upload_data(self):
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            response = requests.post(
                f"{self.server_url}/api/telemetry",
                json=data,
                timeout=2
            )
            
            if response.status_code == 200:
                self.upload_count += 1
                if self.debug:
                    print(f"✓ [{self.upload_count:04d}] Uploaded!")
            else:
                self.error_count += 1
                print(f"✗ Upload failed: HTTP {response.status_code}")
                
        except FileNotFoundError:
            pass  
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
            pass  
        except Exception as e:
            self.error_count += 1
            print(f"✗ Error: {e}")


class TelemetrySyncClient:
    """The main wrapper class you will import into your larger code"""
    def __init__(self, server_url: str, data_file_path: str, debug: bool = True):
        # This is where you give it the JSON file path
        self.server_url = server_url
        self.data_file_path = os.path.abspath(data_file_path)
        self.debug = debug
        
        # Initialize internal handlers and observers
        self.uploader = TelemetryUploaderHandler(self.server_url, self.data_file_path, self.debug)
        self.observer = Observer()
        self.running = False

    def start(self):
        """Starts monitoring the JSON file in a background thread"""
        if self.running:
            print("[INFO] TelemetrySyncClient is already running.")
            return

        # Check server health before initiating thread
        try:
            requests.get(f"{self.server_url}/", timeout=2)
            print(f"✓ Cloud Server is reachable!")
        except Exception:
            print(f"⚠️ WARNING: Cannot reach server at {self.server_url}. Will still monitor and attempt transfers.")

        # Find the directory containing the JSON file to watch it
        watch_dir = os.path.dirname(self.data_file_path) or '.'
        self.observer.schedule(self.uploader, path=watch_dir, recursive=False)
        
        # Kicks off the internal Watchdog background thread automatically
        self.observer.start()
        self.running = True
        print(f"[OK] Background file sync active. Monitoring: {self.data_file_path}")

    def stop(self):
        """Stops the file monitor and gives you final execution reports"""
        if not self.running:
            return
            
        print("\n" + "=" * 60)
        print("🛑 Sync thread stopping...")
        self.observer.stop()
        self.observer.join()
        self.running = False
        print(f"📊 Stats: {self.uploader.upload_count} uploads, {self.uploader.error_count} errors")
        print("=" * 60)
