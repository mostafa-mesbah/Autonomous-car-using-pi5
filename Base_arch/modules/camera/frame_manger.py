import threading
import time

class FrameManager:
    """Manages frame capture and sharing between threads"""
    
    def __init__(self, camera, logger=None):
        self.camera = camera
        self.logger = logger
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.frame_available = threading.Event()
        self.capture_thread_running = False
        self.capture_thread = None
        self.last_capture_time = 0
    
    def start_capture(self):
        """Start the capture thread"""
        if self.capture_thread_running:
            return
            
        self.capture_thread_running = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True,name="CaptureThread"
        )
        self.capture_thread.start()
        print("[FrameManager] Capture thread started (as fast as possible)")
    
    def stop_capture(self):
        """Stop the capture thread"""
        self.capture_thread_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        print("[FrameManager] Capture thread stopped")
    
    def _log(self, key, value):
        """Safely log without crashing"""
        if self.logger is not None:
            try:
                self.logger.update(key, value)
            except Exception as e:
                pass
    
    def _capture_loop(self):
        """Dedicated thread for capturing frames as fast as possible"""
        last_time = time.perf_counter()
        
        while self.capture_thread_running:
            try:
                current_time = time.perf_counter()
                delay_ms = (current_time - last_time) * 1000
                
                # Log the delay between frame capture START times
                self._log("capture_delay_ms", round(delay_ms, 1))
                
                # Update last_time with current START time for next iteration
                last_time = current_time
                
                # Capture the frame
                frame = self.camera.capture()
                
                if frame is not None:
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                        self.frame_available.set()
                        
            except Exception as e:
                pass
                time.sleep(0.01)
    
    def get_current_frame(self, blocking=False, timeout=0.1):
        """Get the latest frame"""
        if blocking:
            if not self.frame_available.wait(timeout=timeout):
                return None
            self.frame_available.clear()
        
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None