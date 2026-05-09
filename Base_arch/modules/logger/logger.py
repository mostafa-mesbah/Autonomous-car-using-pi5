import json
import threading
import os

class CarLogger:
    """Simple logger that works like print() but in another terminal"""
    
    def __init__(self, log_file="/home/mostafa/old_version/Autonomous-car-using-pi5/Base_arch/car_state.json"):
        self.log_file = log_file
        self.lock = threading.Lock()
        self.state = {}
    
    def update(self, variable, value):
        """Update any variable - works just like print but stores state"""
        with self.lock:
            self.state[variable] = value
            self._save()
    
    def update_many(self, **kwargs):
        """Update multiple variables at once"""
        with self.lock:
            for var, val in kwargs.items():
                self.state[var] = val
            self._save()
    
    def _save(self):
        """Save to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.state, f)
        except:
            pass
    
    def clear(self):
        """Clear all variables"""
        with self.lock:
            self.state = {}
            self._save()
