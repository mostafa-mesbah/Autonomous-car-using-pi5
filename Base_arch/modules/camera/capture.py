import cv2
import threading

class CameraCapture:
    """Handles camera initialization and frame capture only"""
    
    def __init__(self, width=640, height=480, camera_index=None):
        self.width = width
        self.height = height
        self.lock = threading.Lock()
        self.camera = None
        self.camera_index = camera_index
        
        # Initialize camera
        self._init_camera()
    
    def _init_camera(self):
        """Initialize camera with given parameters"""
        if self.camera_index is not None:
            # Try specific camera index
            self.camera = cv2.VideoCapture(self.camera_index)
            if not self.camera.isOpened():
                raise RuntimeError(f"Camera at index {self.camera_index} not found!")
        else:
            # Auto-detect camera
            self.camera = self._find_available_camera()
            if self.camera is None:
                raise RuntimeError("No camera found!")
        
        # Set camera properties
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        print(f"[Camera] Initialized with resolution {self.width}x{self.height}")
    
    def _find_available_camera(self, max_index=10):
        """Find first available camera"""
        for i in range(max_index):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"[Camera] Found camera at index {i}")
                return cap
            cap.release()
        return None
    
    def capture(self):
        """Capture a single frame - returns copy for thread safety"""
        with self.lock:
            if self.camera is None:
                return None
            ret, frame = self.camera.read()
            if ret and frame is not None:
                return frame.copy()  # Return a copy to avoid modification issues
            return None
    
    def release(self):
        """Release camera resources"""
        if self.camera:
            self.camera.release()
            print("[Camera] Camera released")
    
    def __del__(self):
        """Destructor to ensure camera is released"""
        self.release()