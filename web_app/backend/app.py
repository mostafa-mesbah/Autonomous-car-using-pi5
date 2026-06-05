"""
Multi-Car Monitoring System - Backend Server
Receives telemetry from Pi clients via HTTP POST /api/telemetry
Serves data to web dashboard via REST API and WebSocket
"""

import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import os
from datetime import datetime

# Get frontend path
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

# Initialize Flask app with static folder serving
app = Flask(__name__, 
            static_folder=frontend_dir,
            static_url_path='')
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# ============= Car State Manager (built-in) =============

class CarStateManager:
    """Manages car states and telemetry history"""
    
    def __init__(self, car_ids, history_max=100):
        self.cars = {}
        self.history_max = history_max
        for car_id in car_ids:
            self.cars[car_id] = self._initial_state(car_id)
    
    def _initial_state(self, car_id):
        return {
            "car_id": car_id,
            "speed": 0,
            "battery": 100,
            "temperature": 25,
            "gps": {"lat": 30.0444, "lon": 31.2357},
            "status": "idle",
            "mode": "manual",
            "destination": None,
            "alerts": [],
            "crash": False,
            "timestamp": datetime.now().isoformat(),
            "history": {"speed": [], "battery": [], "temperature": []},
            "connected": False,
            "traffic_light": "none",
            "detected_sign": "none",
            "yolo_confidence": 0.0,
            "traffic_override": False,
            "servo_angle": 86,
            "mission": "",
            "parking_requested": False
        }
    
    def update(self, data):
        """Update car state from telemetry data"""
        car_id = data.get("car_id")
        
        if car_id not in self.cars:
            # Auto-register new cars
            self.cars[car_id] = self._initial_state(car_id)
        
        car = self.cars[car_id]
        
        # Update telemetry
        car["speed"] = data.get("speed", car["speed"])
        car["battery"] = data.get("battery", car["battery"])
        car["temperature"] = data.get("temperature", car["temperature"])
        car["mode"] = data.get("mode", car["mode"])
        car["timestamp"] = datetime.now().isoformat()
        car["connected"] = True
        
        if "gps" in data:
            car["gps"] = data["gps"]
        
        # Update crash status
        car["crash"] = data.get("crash", False)
        
        # Update status based on speed
        if car["crash"]:
            car["status"] = "alert"
        elif car["speed"] > 0:
            car["status"] = "driving"
        else:
            car["status"] = "idle"
        # YOLO / AI fields — real class names from autonomous_car.py
        car["traffic_light"]    = data.get("traffic_light",    "none")
        car["detected_sign"]    = data.get("detected_sign",    "none")
        car["yolo_confidence"]  = data.get("yolo_confidence",  0.0)
        car["traffic_override"] = data.get("traffic_override", False)
        car["servo_angle"]      = data.get("servo_angle",      86)
        car["mission"]          = data.get("mission",          "")

        # Parking request flag
        if car["detected_sign"] == "parking":
            car["parking_requested"] = True

        # History
        car["history"]["speed"].append(car["speed"])
        car["history"]["battery"].append(car["battery"])
        car["history"].setdefault("temperature", []).append(car["temperature"])
        if len(car["history"]["speed"]) > self.history_max:
            car["history"]["speed"].pop(0)
        if len(car["history"]["battery"]) > self.history_max:
            car["history"]["battery"].pop(0)
        if len(car["history"]["temperature"]) > self.history_max:
            car["history"]["temperature"].pop(0)
        
        # Alerts
        if car["battery"] < 20:
            self._add_alert(car_id, "warning", f"Low battery: {car['battery']}%")
        if car["temperature"] > 45:
            self._add_alert(car_id, "warning", f"High temp: {car['temperature']}°C")
        if car["crash"]:
            self._add_alert(car_id, "critical", "Crash detected!")
        
        return car
    
    def _add_alert(self, car_id, severity, message):
        alert = {
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.cars[car_id]["alerts"].append(alert)
        if len(self.cars[car_id]["alerts"]) > 10:
            self.cars[car_id]["alerts"].pop(0)

# Initialize state manager
state_manager = CarStateManager(config['car_ids'])

print("=" * 50)
print("Multi-Car Monitoring System - Server")
print("Receiving telemetry from Pi clients via /api/telemetry")
print(f"Cars: {', '.join(config['car_ids'])}")
print("=" * 50)


# ============= WebSocket Events =============

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected', 'message': 'Connected to car monitoring system'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on('select_car')
def handle_select_car(data):
    car_id = data.get('car_id')
    if car_id in state_manager.cars:
        car_state = state_manager.cars[car_id]
        emit('car_selected', car_state)
        print(f"Client selected car: {car_id}")
    else:
        emit('error', {'message': f'Car {car_id} not found'})

@socketio.on('set_destination')
def handle_set_destination(data):
    car_id = data.get('car_id')
    lat = data.get('lat')
    lon = data.get('lon')
    if car_id in state_manager.cars:
        state_manager.cars[car_id]['destination'] = {'lat': lat, 'lon': lon}
        emit('destination_set', {'car_id': car_id, 'destination': {'lat': lat, 'lon': lon}})

@socketio.on('emergency_stop')
def handle_emergency_stop(data):
    car_id = data.get('car_id')
    if car_id in state_manager.cars:
        state_manager.cars[car_id]['status'] = 'stopped'
        state_manager.cars[car_id]['speed'] = 0
        emit('car_stopped', {'car_id': car_id})

@socketio.on('change_mode')
def handle_change_mode(data):
    car_id = data.get('car_id')
    mode = data.get('mode')
    if car_id in state_manager.cars:
        state_manager.cars[car_id]['mode'] = mode
        emit('mode_changed', {'car_id': car_id, 'mode': mode})


# ============= REST API =============

@app.route('/')
def index():
    """Serve the main index page"""
    return app.send_static_file('index.html')

@app.route('/dashboard.html')
def dashboard():
    """Serve dashboard page"""
    return app.send_static_file('dashboard.html')

@app.route('/api')
def api_info():
    """API information"""
    return jsonify({
        'name': 'Multi-Car Monitoring System API',
        'version': '1.0',
        'endpoints': {
            'GET /api/cars': 'Get all car states',
            'GET /api/car/<car_id>': 'Get specific car state',
            'POST /api/telemetry': 'Receive telemetry from Pi client'
        }
    })

@app.route('/api/cars')
def get_all_cars():
    return jsonify(state_manager.cars)

@app.route('/api/car/<car_id>')
def get_car(car_id):
    car_state = state_manager.cars.get(car_id)
    if car_state:
        return jsonify(car_state)
    return jsonify({'error': 'Car not found'}), 404

@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    """
    Receive telemetry data from Pi clients
    Pi writes sensor data to JSON file, sync script uploads here
    """
    try:
        data = request.get_json()
        
        if not data or 'car_id' not in data:
            return jsonify({'error': 'Invalid data: car_id required'}), 400
        
        # Update state
        car_state = state_manager.update(data)
        
        if car_state:
            # Broadcast to all dashboard clients via WebSocket
            socketio.emit('telemetry_update', {data['car_id']: car_state})
            
            return jsonify({
                'status': 'success',
                'car_id': data['car_id'],
                'timestamp': car_state['timestamp']
            }), 200
        else:
            return jsonify({'error': 'Failed to process telemetry'}), 500
        return jsonify({'error': 'Invalid car_id'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear_alerts/<car_id>', methods=['POST'])
def clear_alerts(car_id):
    if car_id in state_manager.cars:
        state_manager.cars[car_id]['alerts'] = []
        return jsonify({'status': 'cleared'})
    return jsonify({'error': 'Car not found'}), 404


# ============= Startup =============

if __name__ == '__main__':
    import socket
    
    # Get laptop's actual network IP (not loopback)
    def get_network_ip():
        try:
            # Connect to external address to get network interface IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Google DNS
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "192.168.1.12"  # Fallback
    
    local_ip = get_network_ip()
    
    print("\n" + "=" * 60)
    print("Multi-Car Monitoring System - Backend Server")
    print("=" * 60)
    print(f"Cars: {', '.join(config['car_ids'])}")
    print("=" * 60)

    print("\n[OK] SERVER READY!")
    print("\n[*] Access from this laptop:")
    print("   http://localhost:5000")
    print("   http://127.0.0.1:5000")

    print(f"\n[*] Access from ANY device on network:")
    print(f"   http://{local_ip}:5000")

    print("\n" + "=" * 60 + "\n")
    
    # Run Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
