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
import logging           # <-- 1. Add this import
from flask import Flask, Response, jsonify, render_template, request

# Import your lane detection function
from modules.lane_detector import process_lane

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# Global variables
current_left_angle = 0
current_right_angle = 0

current_left_direction = "--"
current_right_direction = "--"

current_left_mission = "--"
current_right_mission = "--"
current_left_length = 0
current_right_length = 0

final_angle = 0
final_direction = "--"
final_mission = "--"

current_debug_info = None
fps = 0
camera_running = False
video_paused = False
current_source = "camera"
video_total_frames = 0
video_current_frame = 0
video_seek_target = None
video_stream_fps = 0.0

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

def apply_lane_result(result):
    """Normalize lane.py return values into the global state."""
    global current_debug_info, final_mission, final_direction, final_angle
    global current_left_angle, current_right_angle
    global current_left_direction, current_right_direction
    global current_left_mission, current_right_mission
    global current_left_length, current_right_length

    if len(result) == 12:
        (
            mission_from_left,
            direction_from_left,
            angle_left,
            left_length,
            mission_from_right,
            direction_from_right,
            angle_right,
            right_length,
            final_mission_value,
            final_direction_value,
            final_angle_value,
            debug_info,
        ) = result
    else:
        raise ValueError(f"Unexpected lane result format: {len(result)}")

    # Update left lane global variables
    current_left_mission = mission_from_left
    current_left_direction = direction_from_left
    current_left_angle = angle_left
    current_left_length = left_length

    # Update right lane global variables
    current_right_mission = mission_from_right
    current_right_direction = direction_from_right
    current_right_angle = angle_right
    current_right_length = right_length

    # Update the final decision variables
    final_mission = final_mission_value
    final_direction = final_direction_value
    final_angle = final_angle_value
    
    current_debug_info = debug_info

def process_camera(camera_id=1):
    """Background thread to process camera frames"""
    global fps, camera_running
    
    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    
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
            apply_lane_result(result)
            
            mission = final_mission
            direction = final_direction
            angle = final_angle
            
            # Calculate FPS
            frame_count += 1
            if time.time() - last_time >= 1.0:
                fps = frame_count
                frame_count = 0
                last_time = time.time()
                print(
                    f"[INFO] FPS: {fps} | "
                    f"Left: angle={current_left_angle:.1f} dir={current_left_direction} mission={current_left_mission} len={current_left_length:.1f} | "
                    f"Right: angle={current_right_angle:.1f} dir={current_right_direction} mission={current_right_mission} len={current_right_length:.1f} | "
                    f"Final: angle={final_angle:.1f} mission={final_mission} dir={final_direction}"
                )
            
        except Exception as e:
            print(f"[ERROR] Processing error: {e}")
            import traceback
            #traceback.print_exc()
        
        time.sleep(0.001)  # Small delay to prevent CPU overload
    
    cap.release()
    print("[INFO] Camera stopped")

def process_video(video_path):
    global fps, camera_running, video_paused
    global video_total_frames, video_current_frame, video_seek_target, video_stream_fps
    global current_left_angle, current_right_angle
    global current_left_direction, current_right_direction
    global current_left_mission, current_right_mission
    global current_left_length, current_right_length
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"[ERROR] Cannot open {video_path}")
        return

    video_fps = cap.get(cv2.CAP_PROP_FPS)

    if video_fps <= 0:
        video_fps = 30

    video_stream_fps = float(video_fps)
    video_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    video_current_frame = 0
    video_seek_target = None

    print(f"[INFO] Video FPS = {video_fps}")

    frame_count = 0
    last_time = time.time()

    while camera_running:

        if video_seek_target is not None:
            target_frame = max(0, min(int(video_seek_target), max(video_total_frames - 1, 0)))
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            video_seek_target = None

        if video_paused:
            time.sleep(0.05)
            continue

        ret, frame = cap.read()

        if not ret:
            print("[INFO] End of video")
            break

        try:
            result = process_lane(frame, return_debug=True)
            apply_lane_result(result)
            video_current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES) or 0)

        except Exception as e:
            print(f"[ERROR] Processing video frame error: {e}")

        frame_count += 1

        if time.time() - last_time >= 1:
            fps = frame_count
            frame_count = 0
            last_time = time.time()
            print(
                f"[INFO] FPS: {fps} | "
                f"Left: angle={current_left_angle:.1f} dir={current_left_direction} mission={current_left_mission} len={current_left_length:.1f} | "
                f"Right: angle={current_right_angle:.1f} dir={current_right_direction} mission={current_right_mission} len={current_right_length:.1f} | "
                f"Final: angle={final_angle:.1f} mission={final_mission} dir={final_direction}"
            )

        # HALF SPEED playback
        time.sleep(2.0 / video_fps)

    cap.release()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/get_frames')
def get_frames():
    """Return all frames and stats as JSON with base64 encoding"""
    global current_debug_info, final_mission, final_direction, final_angle, fps
    global current_left_angle, current_right_angle
    global current_left_direction, current_right_direction
    global current_left_mission, current_right_mission
    global current_left_length, current_right_length
    global video_paused, current_source
    global video_total_frames, video_current_frame, video_stream_fps
    
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
            'final_angle': 0,
            'final_direction': '--',
            'final_mission': '--',
            'final_steer': 0,
            'left_angle': 0,
            'right_angle': 0,
            'left_direction': '--',
            'right_direction': '--',
            'left_mission': '--',
            'right_mission': '--',
            'left_length': 0,
            'right_length': 0,
            'left_line': None,
            'right_line': None,
            'frame_shape': None,
            'video_paused': bool(video_paused),
            'is_video_source': current_source == 'video',
            'video_total_frames': int(video_total_frames),
            'video_current_frame': int(video_current_frame),
            'video_fps': float(video_stream_fps),
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
        left_line = current_debug_info.get('left_line')
        right_line = current_debug_info.get('right_line')
        original_frame = current_debug_info.get('original')
        frame_shape = list(original_frame.shape) if original_frame is not None else None
        
        return jsonify({
            'original': original_b64,
            'cropped': cropped_b64,
            'gray': gray_b64,
            'binary': binary_b64,
            'dilated': dilated_b64,
            'result': result_b64,
            'angle': float(final_angle),
            'direction': str(final_direction),
            'mission': str(final_mission),
            'final_angle': float(final_angle),
            'final_direction': str(final_direction),
            'final_mission': str(final_mission),
            'final_steer': float(final_angle),
            'left_angle': float(current_left_angle),
            'right_angle': float(current_right_angle),
            'left_direction': str(current_left_direction),
            'right_direction': str(current_right_direction),
            'left_mission': str(current_left_mission),
            'right_mission': str(current_right_mission),
            'left_length': float(current_left_length),
            'right_length': float(current_right_length),
            'left_line': left_line,
            'right_line': right_line,
            'frame_shape': frame_shape,
            'video_paused': bool(video_paused),
            'is_video_source': current_source == 'video',
            'video_total_frames': int(video_total_frames),
            'video_current_frame': int(video_current_frame),
            'video_fps': float(video_stream_fps),
            'fps': int(fps),
            'timestamp': time.strftime('%H:%M:%S')
        })
    except Exception as e:
        print(f"[ERROR] get_frames error: {e}")
        return jsonify({'error': str(e)})

@app.route('/video/play', methods=['POST'])
def video_play():
    global video_paused, current_source
    if current_source != 'video':
        return jsonify({'ok': False, 'error': 'Video controls are only available in video source mode'})
    video_paused = False
    return jsonify({'ok': True, 'video_paused': video_paused})

@app.route('/video/pause', methods=['POST'])
def video_pause():
    global video_paused, current_source
    if current_source != 'video':
        return jsonify({'ok': False, 'error': 'Video controls are only available in video source mode'})
    video_paused = True
    return jsonify({'ok': True, 'video_paused': video_paused})

@app.route('/video/seek', methods=['POST'])
def video_seek():
    global video_seek_target, current_source, video_total_frames
    if current_source != 'video':
        return jsonify({'ok': False, 'error': 'Video controls are only available in video source mode'})

    payload = request.get_json(silent=True) or {}
    frame = payload.get('frame')
    if frame is None:
        return jsonify({'ok': False, 'error': 'Missing frame value'})

    try:
        frame = int(frame)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Invalid frame value'})

    max_frame = max(video_total_frames - 1, 0)
    frame = max(0, min(frame, max_frame))
    video_seek_target = frame
    return jsonify({'ok': True, 'target_frame': frame})

def main():
    parser = argparse.ArgumentParser(description='Lane Detection Web Debugger')
    parser.add_argument('--source', type=str, choices=['camera','image','video'], default='camera',
                       help='Input source')
    parser.add_argument('--image', type=str, default=None,
                       help='Path to image file')
    parser.add_argument('--video', type=str, default=None,
                        help='Path to mp4 file')
    parser.add_argument('--camera_id', type=int, default=0,
                       help='Camera device ID')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Flask host')
    parser.add_argument('--port', type=int, default=5000,
                       help='Flask port')
    
    args = parser.parse_args()
    
    global camera_running, current_source, video_paused
    global video_total_frames, video_current_frame, video_seek_target, video_stream_fps

    current_source = args.source
    video_paused = False
    video_total_frames = 0
    video_current_frame = 0
    video_seek_target = None
    video_stream_fps = 0.0
    
    if args.source == 'camera':
        camera_running = True
        # Start camera processing in background thread
        process_thread = threading.Thread(target=process_camera, args=(args.camera_id,))
        process_thread.daemon = True
        process_thread.start()
        
        print(f"\n[INFO] Starting web server (Camera Mode)...")
        print(f"[INFO] Open browser and go to: http://{args.host}:{args.port}")
        print(f"[INFO] Press Ctrl+C to stop\n")
        
        try:
            app.run(host=args.host, port=args.port, debug=False, threaded=True)
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
        finally:
            camera_running = False

    elif args.source == 'video':
        if not args.video:
            print("Please provide --video path when using video source")
            return
            
        camera_running = True
        process_thread = threading.Thread(target=process_video, args=(args.video,))
        process_thread.daemon = True
        process_thread.start()
        
        print(f"\n[INFO] Starting web server (Video Mode)...")
        print(f"[INFO] Open browser and go to: http://{args.host}:{args.port}")
        print(f"[INFO] Press Ctrl+C to stop\n")
        
        try:
            app.run(host=args.host, port=args.port, debug=False, threaded=True)
        except KeyboardInterrupt:
            print("\n[INFO] Shutting down...")
        finally:
            camera_running = False
            
    elif args.source == 'image':
        # Image mode - process once
        if not args.image:
            print("Please provide --image path when using image source")
            return
        
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"Could not load image: {args.image}")
            return
        
        result = process_lane(frame, return_debug=True)
        apply_lane_result(result)
        
        mission = final_mission
        direction = final_direction
        angle = final_angle
        
        print(f"\n[INFO] Processing single image...")
        print(f"[INFO] Angle: {angle:.1f}°, Direction: {direction}, Mission: {mission}")
        print(f"[INFO] Open browser and go to: http://{args.host}:{args.port}")
        print(f"[INFO] Press Ctrl+C to stop\n")
        
        app.run(host=args.host, port=args.port, debug=False, threaded=True)

if __name__ == "__main__":
    main()