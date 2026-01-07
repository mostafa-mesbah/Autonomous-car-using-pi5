import time
from flask import Flask, Response
import cv2
import numpy as np
from ultralytics import YOLO
import threading


class ModelControl:
    def __init__(self, path, width=640, height=480, infer_size=(320, 320)):
        self.lock = threading.Lock()
        self.model_path = path
        self.default_conf = 0.6
        self.infer_size = infer_size
        
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Load YOLO model
        self.model = YOLO(self.model_path)
        
        # Flask app with only one route
        self.app = Flask(__name__)
        
        # Single route for the stream
        @self.app.route('/')
        def stream():
            return Response(self.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

    def capture(self):
        with self.lock:
            frame = camera.read()
            return frame
    def detect(self, frame):
        detections = [] 
        results = self.model(frame, imgsz=self.infer_size, conf=self.default_conf, verbose=False)
        
        for box in results[0].boxes:
            coords = box.xyxy[0].cpu().numpy()  # x1, y1, x2, y2
            x1, y1, x2, y2 = coords
            box_area = (x2 - x1) * (y2 - y1)  # area of the bounding box
            
            cls = int(box.cls.cpu().item())
            conf = box.conf.cpu().item()
            
            # Append class, confidence, coordinates, and area
            detections.append((self.model.names[cls], conf, (x1, y1, x2, y2), box_area))
        
        return detections

    def generate_frames(self):
        """Continuously capture frames, draw detections and areas, and yield them as JPEG."""
        while True:
            frame = self.capture()
            frame = cv2.flip(frame, -1)  # optional flip

            detections = self.detect(frame)

            for cls, conf, (x1, y1, x2, y2), area in detections:
                # Draw rectangle
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                
                # Draw class + confidence + area
                label = f"{cls} {conf:.2f} area={int(area)}"
                cv2.putText(frame, label, (int(x1), int(y1)-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Encode frame as JPEG
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
