import time
from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import numpy as np
from ultralytics import YOLO
import threading

class ModelControl:
    def __init__(self, path, width=640, height=480, infer_size=(320, 320)):
        self.lock = threading.Lock()
        self.model_path = path
        self.default_conf = 0.8
        self.infer_size = infer_size
        
        # Initialize camera
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"}
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(2)
        
        # Load YOLO model
        self.model = YOLO(self.model_path)
        
        # Flask app with only one route
        self.app = Flask(__name__)
        
        # Single route for the stream
        @self.app.route('/')
        def stream():
            return Response(self.generate_frames(),
                           mimetype='multipart/x-mixed-replace; boundary=frame')

    def capture_and_detect(self):
        with self.lock:
            frame = self.picam2.capture_array()
            results = self.model(frame, imgsz=self.infer_size, conf=self.default_conf, verbose=False)

            detections = []  # To store detected classes and confidence

            # Draw boxes and labels
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    cls = int(box.cls.cpu().item())
                    conf = box.conf.cpu().item()
                    label = f"{self.model.names[cls]} {conf:.2f}"

                    # Append detection info
                    detections.append((self.model.names[cls], conf))

                    # Draw on frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Return both the frame and the detections
            return frame, detections

    def generate_frames(self):
        """Continuously capture frames and yield them as JPEG for the HTTP stream."""
        while True:
            frame, detections = self.capture_and_detect()
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    def start_stream(self, host="0.0.0.0", port=5000):
        """Start the Flask streaming server."""
        print(f"Starting video stream at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False, use_reloader=False)
