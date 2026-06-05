"""
Camera Module for MJPEG Streaming
Captures video and streams as MJPEG (240p resolution)
"""
import cv2
import threading
import time
from typing import Optional

class CameraStream:
    def __init__(self, camera_index: int = 0, resolution: tuple = (320, 240)):
        self.camera_index = camera_index
        self.resolution = resolution
        self.camera: Optional[cv2.VideoCapture] = None
        self.frame = None
        self.running = False
        self.lock = threading.Lock()
        self.thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start camera capture thread"""
        if self.running:
            print("Camera already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        print(f"Camera started (index: {self.camera_index}, resolution: {self.resolution})")
    
    def stop(self):
        """Stop camera capture"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        if self.camera:
            self.camera.release()
        print("Camera stopped")
    
    def _capture_loop(self):
        """Main capture loop"""
        while self.running:
            # Try to open camera if not open
            if self.camera is None or not self.camera.isOpened():
                self.camera = cv2.VideoCapture(self.camera_index)
                
                if not self.camera.isOpened():
                    print(f"Failed to open camera {self.camera_index}")
                    time.sleep(5)
                    continue
                
                # Set resolution
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                self.camera.set(cv2.CAP_PROP_FPS, 15)  # 15 FPS for 240p
            
            # Capture frame
            ret, frame = self.camera.read()
            
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                print("Failed to read frame")
                if self.camera:
                    self.camera.release()
                    self.camera = None
                time.sleep(1)
    
    def get_frame(self) -> Optional[bytes]:
        """Get current frame as JPEG bytes"""
        with self.lock:
            if self.frame is None:
                return None
            
            # Encode frame as JPEG
            ret, jpeg = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            
            if ret:
                return jpeg.tobytes()
            return None
    
    def generate_frames(self):
        """Generator for MJPEG stream"""
        while True:
            frame_bytes = self.get_frame()
            
            if frame_bytes is None:
                # Send placeholder frame
                time.sleep(0.1)
                continue
            
            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.066)  # ~15 FPS


class MockCameraStream:
    """Mock camera for testing without actual camera hardware"""
    def __init__(self):
        import numpy as np
        self.frame_count = 0
    
    def start(self):
        print("Mock camera started (generating test frames)")
    
    def stop(self):
        print("Mock camera stopped")
    
    def get_frame(self) -> bytes:
        """Generate a test frame"""
        import numpy as np
        
        # Create a simple test image
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Add some pattern
        img[::20, :] = [0, 255, 0]  # Green horizontal lines
        img[:, ::20] = [0, 0, 255]  # Red vertical lines
        
        # Add frame counter text
        cv2.putText(img, f"Frame: {self.frame_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, "Mock Camera", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        self.frame_count += 1
        
        # Encode as JPEG
        ret, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return jpeg.tobytes()
    
    def generate_frames(self):
        """Generator for mock MJPEG stream"""
        while True:
            frame_bytes = self.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.066)  # ~15 FPS
