#!/usr/bin/env python3
"""
Simple Flask web server to visualize lane detection pipeline
"""

import cv2
import numpy as np
import argparse
import threading
import time
import base64
from flask import Flask, render_template_string, Response, jsonify

# Import your lane detection function
from modules.lane_detector import process_lane

app = Flask(__name__)

# Global variables
current_debug_info = None
current_mission = "s"
current_direction = "stop"
current_angle = 0
fps = 0
camera_running = False

# HTML Template (fixed - removed /info endpoint calls)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Lane Detection Debugger</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            margin: 0;
            padding: 20px;
        }
        h1 {
            text-align: center;
            margin-bottom: 20px;
            color: #00ff88;
        }
        .container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
        }
        .pipeline {
            flex: 2;
            min-width: 800px;
            background: #0f0f1a;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }
        .info {
            flex: 1;
            min-width: 300px;
            background: #0f0f1a;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }
        .stage-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stage-card {
            background: #1a1a2e;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
        }
        .stage-title {
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #ffaa00;
        }
        .stage-image {
            width: 100%;
            height: auto;
            border-radius: 5px;
            border: 1px solid #333;
            background: #000;
            min-height: 150px;
        }
        .info-card {
            background: #1a1a2e;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .info-label {
            font-size: 12px;
            color: #888;
            margin-bottom: 5px;
        }
        .info-value {
            font-size: 28px;
            font-weight: bold;
            color: #00ff88;
        }
        .angle-value {
            color: #ffaa00;
            font-size: 36px;
        }
        .mission-value {
            color: #00aaff;
        }
        .fps-value {
            color: #ff66cc;
        }
        .status {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: bold;
        }
        .status-running {
            background: #00ff8822;
            color: #00ff88;
            border: 1px solid #00ff88;
        }
        hr {
            border-color: #333;
            margin: 15px 0;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .live-badge {
            animation: pulse 2s infinite;
        }
        .error-message {
            color: #ff4444;
            background: #440000;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>🚗 Lane Detection Pipeline Debugger</h1>
    
    <div class="container">
        <div class="pipeline">
            <div style="margin-bottom: 15px;">
                <span class="status status-running live-badge">🟢 LIVE</span>
                <span style="float: right;">Processing FPS: <span id="fps_display">0</span></span>
            </div>
            
            <div class="stage-grid">
                <div class="stage-card">
                    <div class="stage-title">📷 1. Original Frame</div>
                    <img id="img_original" class="stage-image" src="data:image/jpeg;base64,...">
                </div>
                <div class="stage-card">
                    <div class="stage-title">✂️ 2. Cropped ROI</div>
                    <img id="img_cropped" class="stage-image" src="data:image/jpeg;base64,...">
                </div>
                <div class="stage-card">
                    <div class="stage-title">⚫ 3. Grayscale</div>
                    <img id="img_gray" class="stage-image" src="data:image/jpeg;base64,...">
                </div>
                <div class="stage-card">
                    <div class="stage-title">🔲 4. Binary</div>
                    <img id="img_binary" class="stage-image" src="data:image/jpeg;base64,...">
                </div>
                <div class="stage-card">
                    <div class="stage-title">🔍 5. Dilated</div>
                    <img id="img_dilated" class="stage-image" src="data:image/jpeg;base64,...">
                </div>
                <div class="stage-card">
                    <div class="stage-title">🎯 6. Result (Red Line)</div>
                    <img id="img_result" class="stage-image" src="data:image/jpeg;base64,...">
                </div>
            </div>
        </div>
        
        <div class="info">
            <h3>📊 Detection Results</h3>
            
            <div class="info-card">
                <div class="info-label">🎯 Current Angle</div>
                <div class="info-value angle-value" id="angle_display">0<span style="font-size: 20px;">°</span></div>
            </div>
            
            <div class="info-card">
                <div class="info-label">🧭 Direction</div>
                <div class="info-value" id="direction_display">--</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">📡 Mission Command</div>
                <div class="info-value mission-value" id="mission_display">--</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">⚡ Processing FPS</div>
                <div class="info-value fps-value" id="fps_value">0</div>
            </div>
            
            <hr>
            
            <div class="info-card">
                <div class="info-label">📊 Status</div>
                <div id="status_display" style="color: #00ff88;">Running</div>
            </div>
            
            <div class="info-card">
                <div class="info-label">⏱️ Last Update</div>
                <div id="timestamp_display" style="color: #888;">--</div>
            </div>
        </div>
    </div>
    
    <script>
        function updateAll() {
            fetch('/get_frames')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error('Error:', data.error);
                        return;
                    }
                    
                    if (data.original) {
                        document.getElementById('img_original').src = 'data:image/jpeg;base64,' + data.original;
                        document.getElementById('img_cropped').src = 'data:image/jpeg;base64,' + data.cropped;
                        document.getElementById('img_gray').src = 'data:image/jpeg;base64,' + data.gray;
                        document.getElementById('img_binary').src = 'data:image/jpeg;base64,' + data.binary;
                        document.getElementById('img_dilated').src = 'data:image/jpeg;base64,' + data.dilated;
                        document.getElementById('img_result').src = 'data:image/jpeg;base64,' + data.result;
                        
                        document.getElementById('angle_display').innerHTML = data.angle + '<span style="font-size: 20px;">°</span>';
                        document.getElementById('direction_display').innerHTML = data.direction;
                        document.getElementById('mission_display').innerHTML = data.mission;
                        document.getElementById('fps_display').innerHTML = data.fps;
                        document.getElementById('fps_value').innerHTML = data.fps;
                        document.getElementById('timestamp_display').innerHTML = data.timestamp;
                    }
                })
                .catch(error => {
                    console.error('Fetch error:', error);
                });
        }
        
        // Update every 100ms
        setInterval(updateAll, 100);
        
        // Initial update
        updateAll();
    </script>
</body>
</html>
"""

def encode_frame_to_base64(frame):
    """Convert OpenCV frame to base64 string safely"""
    if frame is None:
        return None
    
    try:
        # Make sure frame is valid
        if frame.size == 0:
            return None
        
        # Encode as JPEG
        success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not success:
            return None
        
        return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Encoding failed: {e}")
        return None

def process_camera(camera_id=1):
    """Background thread to process camera frames"""
    global current_debug_info, current_mission, current_direction, current_angle, fps, camera_running
    
    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("[ERROR] Could not open camera")
        return
    
    print("[INFO] Camera started")
    
    frame_count = 0
    last_time = time.time()
    
    while camera_running:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to grab frame")
            time.sleep(0.01)
            continue
        
        try:
            # Process lane detection with debug info
            result = process_lane(frame, return_debug=True)
            
            # Handle different return formats
            if len(result) == 4:
                mission, direction, angle, debug_info = result
            else:
                print(f"[ERROR] Unexpected return format: {len(result)}")
                continue
            
            # Update global variables
            current_mission = mission
            current_direction = direction
            current_angle = angle
            current_debug_info = debug_info
            
            # Calculate FPS
            frame_count += 1
            if time.time() - last_time >= 1.0:
                fps = frame_count
                frame_count = 0
                last_time = time.time()
                print(f"[INFO] FPS: {fps}, Angle: {angle:.1f}°, Mission: {mission}, Direction: {direction}")
            
        except Exception as e:
            print(f"[ERROR] Processing error: {e}")
            import traceback
            traceback.print_exc()
        
        time.sleep(0.001)  # Small delay to prevent CPU overload
    
    cap.release()
    print("[INFO] Camera stopped")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_frames')
def get_frames():
    """Return all frames as JSON with base64 encoding"""
    global current_debug_info, current_mission, current_direction, current_angle, fps
    
    if current_debug_info is None:
        return jsonify({
            'error': 'No frames yet',
            'original': None,
            'cropped': None,
            'gray': None,
            'binary': None,
            'dilated': None,
            'result': None,
            'angle': 0,
            'direction': '--',
            'mission': '--',
            'fps': 0,
            'timestamp': time.strftime('%H:%M:%S')
        })
    
    try:
        # Create visualization with red line
        vis = current_debug_info.get('visualization')
        if vis is None:
            vis = current_debug_info.get('dilated')
            if vis is not None:
                vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)
        
        # Encode all frames
        original_b64 = encode_frame_to_base64(current_debug_info.get('original'))
        cropped_b64 = encode_frame_to_base64(current_debug_info.get('cropped'))
        gray_b64 = encode_frame_to_base64(current_debug_info.get('gray'))
        binary_b64 = encode_frame_to_base64(current_debug_info.get('binary'))
        dilated_b64 = encode_frame_to_base64(current_debug_info.get('dilated'))
        result_b64 = encode_frame_to_base64(vis)
        
        return jsonify({
            'original': original_b64,
            'cropped': cropped_b64,
            'gray': gray_b64,
            'binary': binary_b64,
            'dilated': dilated_b64,
            'result': result_b64,
            'angle': float(current_angle),
            'direction': str(current_direction),
            'mission': str(current_mission),
            'fps': int(fps),
            'timestamp': time.strftime('%H:%M:%S')
        })
    except Exception as e:
        print(f"[ERROR] get_frames error: {e}")
        return jsonify({'error': str(e)})

def main():
    parser = argparse.ArgumentParser(description='Lane Detection Web Debugger')
    parser.add_argument('--source', type=str, choices=['camera', 'image'], default='camera',
                       help='Input source')
    parser.add_argument('--image', type=str, default=None,
                       help='Path to image file')
    parser.add_argument('--camera_id', type=int, default=0,
                       help='Camera device ID')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Flask host')
    parser.add_argument('--port', type=int, default=5000,
                       help='Flask port')
    
    args = parser.parse_args()
    
    global camera_running
    
    if args.source == 'camera':
        camera_running = True
        # Start camera processing in background thread
        process_thread = threading.Thread(target=process_camera, args=(args.camera_id,))
        process_thread.daemon = True
        process_thread.start()
        
        print(f"\n[INFO] Starting web server...")
        print(f"[INFO] Open browser and go to: http://{args.host}:{args.port}")
        print(f"[INFO] Press Ctrl+C to stop\n")
        
        try:
            app.run(host=args.host, port=args.port, debug=False, threaded=True)
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
        finally:
            camera_running = False
            
    else:
        # Image mode - process once
        if not args.image:
            print("Please provide --image path when using image source")
            return
        
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"Could not load image: {args.image}")
            return
        
        result = process_lane(frame, return_debug=True)
        
        if len(result) == 4:
            mission, direction, angle, debug_info = result
        else:
            print(f"Unexpected return format")
            return
        
        # Store for web display
        current_debug_info = debug_info
        current_mission = mission
        current_direction = direction
        current_angle = angle
        
        print(f"\n[INFO] Processing single image...")
        print(f"[INFO] Angle: {angle:.1f}°, Direction: {direction}, Mission: {mission}")
        print(f"[INFO] Open browser and go to: http://{args.host}:{args.port}")
        print(f"[INFO] Press Ctrl+C to stop\n")
        
        app.run(host=args.host, port=args.port, debug=False, threaded=True)

if __name__ == "__main__":
    main()