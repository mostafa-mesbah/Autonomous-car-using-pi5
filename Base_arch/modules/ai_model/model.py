import time
from ultralytics import YOLO
import threading

class ModelControl:
    """Handles YOLO model initialization and detection only"""
    
    def __init__(self, model_path, infer_size=(320, 320), conf_threshold=0.6):
        self.model_path = model_path
        self.infer_size = infer_size
        self.conf_threshold = conf_threshold
        self.lock = threading.Lock()
        
        # Load YOLO model
        print(f"[Model] Loading model from {model_path}")
        self.model = YOLO(model_path,task="detect")
        print("[Model] Model loaded successfully")
    
    def detect(self, frame):
        """Run detection on a single frame - returns detections only"""
        if frame is None:
            return []
        
        with self.lock:
            results = self.model(frame, imgsz=self.infer_size, 
                                conf=self.conf_threshold, verbose=False)
        
        detections = []
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                coords = box.xyxy[0].cpu().numpy()  # x1, y1, x2, y2
                x1, y1, x2, y2 = coords
                box_area = (x2 - x1) * (y2 - y1)
                
                cls = int(box.cls.cpu().item())
                conf = box.conf.cpu().item()
                class_name = self.model.names[cls]
                
                detections.append((class_name, conf, (x1, y1, x2, y2), box_area))
        
        return detections