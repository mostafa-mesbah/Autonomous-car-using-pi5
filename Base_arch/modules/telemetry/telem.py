import json
import threading
import os
import tempfile
from pathlib import Path
from datetime import datetime

class TelemetryData:
    """Reads and updates telemetry JSON file in place securely"""

    def __init__(self, filepath="/home/uav/grad/Autonomous-car-using-pi5/Base_arch/fils/car_telemetry.json"):
        self.filepath = Path(filepath)
        self._lock = threading.Lock()

        # Read existing file to preserve car_id and any existing data
        self._data = self._read()

    def _read(self):
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[TELEMETRY] Read error: {e}")
            return {}

    def _flush(self):
        """Safely writes telemetry data using an atomic swap to prevent race conditions"""
        with self._lock:
            self._data["timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            snapshot = dict(self._data)
            
        try:
            # 1. Get the directory where the telemetry file lives
            parent_dir = self.filepath.parent
            
            # 2. Create a hidden temporary file in that exact same directory
            with tempfile.NamedTemporaryFile('w', dir=parent_dir, delete=False) as tf:
                json.dump(snapshot, tf, indent=2)
                temp_file_path = tf.name
            
            # 3. Instantly swap the temp file over the real telemetry file.
            # This is an atomic operation on Linux—it has NO middle state where the file is 0 bytes!
            os.replace(temp_file_path, self.filepath)
            
        except Exception as e:
            print(f"[TELEMETRY] Write error: {e}")

    def update(self, key, value):
        """Update a top-level field — car_id is protected"""
        if key == "car_id":
            print("[TELEMETRY] car_id is read-only")
            return
        with self._lock:
            self._data[key] = value
        self._flush()

    def update_nested(self, section, key, value):
        """Update a nested field e.g. update_nested('gps', 'lat', 30.04)"""
        with self._lock:
            self._data[section][key] = value
        self._flush()

    def update_bulk(self, updates: dict):
        """Update multiple fields at once — car_id is protected"""
        updates.pop("car_id", None)  # silently remove car_id if passed
        with self._lock:
            self._data.update(updates)
        self._flush()