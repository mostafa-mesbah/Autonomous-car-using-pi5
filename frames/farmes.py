from picamera2 import Picamera2
from datetime import datetime
import cv2
import os
import threading

class CameraHandler:
    def __init__(self):
        self.picam2 = Picamera2()
        
        # Configure camera
        config = self.picam2.create_still_configuration()
        self.picam2.configure(config)
        self.picam2.start()

        # Lock for thread safety
        self.lock = threading.Lock()

    def capture(self):
        with self.lock:
            # Capture image as numpy array
            frame = self.picam2.capture_array()

            # Create filename with timestamp
            filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".jpg"
            filepath = os.path.join(os.getcwd(), filename)

            # Save the image
            cv2.imwrite(filepath, frame)

            print(f"Saved: {filepath}")
            return frame


if __name__ == "__main__":
    camera = CameraHandler()

    # Capture a single image
    img = camera.capture()

    # Show the image (optional)
    cv2.imshow("Captured", img)
    cv2.waitKey(2000)
    cv2.destroyAllWindows()
