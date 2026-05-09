from flask import Flask, Response
import cv2
import threading

class VideoStreamer:
    """Handles video streaming separately from model detection"""
    
    def __init__(self, camera, model, flip_frame=True):
        self.camera = camera
        self.model = model
        self.flip_frame = flip_frame
        self.app = Flask(__name__)
        
        @self.app.route('/')
        def stream():
            return Response(self._generate_frames(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
    
    def _generate_frames(self):
        """Generate frames with detections for streaming"""
        while True:
            # Get frame from camera
            frame = self.camera.capture()
            if frame is None:
                continue
            
            # Optional flip
            if self.flip_frame:
                frame = cv2.flip(frame, -1)
            
            # Run detection
            detections = self.model.detect(frame)
            
            # Draw detections
            for cls, conf, (x1, y1, x2, y2), area in detections:
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                label = f"{cls} {conf:.2f} area={int(area)}"
                cv2.putText(frame, label, (int(x1), int(y1)-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    def start(self, host="0.0.0.0", port=5000):
        """Start the streaming server"""
        print(f"Starting video stream at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=False, use_reloader=False)