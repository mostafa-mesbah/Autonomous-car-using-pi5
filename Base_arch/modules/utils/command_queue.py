import queue

class CommandQueue:
    """Manages command queues for missions and user inputs"""
    
    def __init__(self):
        self.mission_queue = queue.Queue(maxsize=1)
        self.parking_queue = queue.Queue(maxsize=1)
        self.user_queue = queue.Queue(maxsize=1)
    
    def add_mission_command(self, command):
        """Add mission command from detection/lane threads"""
        if command:
            self.mission_queue.put(command)
    
    def add_parking_request(self):
        """Add parking request"""
        self.parking_queue.put("parking_request")
    
    def add_user_command(self, command):
        """Add user command"""
        if command:
            self.user_queue.put(command)
    
    def get_mission_command(self, timeout=0.1):
        """Get mission command (non-blocking)"""
        try:
            return self.mission_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_parking_request(self, timeout=0.1):
        """Get parking request (non-blocking)"""
        try:
            return self.parking_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_user_command(self, timeout=0.1):
        """Get user command (non-blocking)"""
        try:
            return self.user_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def clear_all(self):
        """Clear all queues"""
        while not self.mission_queue.empty():
            self.mission_queue.get()
        while not self.parking_queue.empty():
            self.parking_queue.get()
        while not self.user_queue.empty():
            self.user_queue.get()
    
    def has_parking_request(self):
        """Check if there's a parking request pending"""
        return not self.parking_queue.empty()