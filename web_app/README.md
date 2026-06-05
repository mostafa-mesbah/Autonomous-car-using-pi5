# Autonomous Multi-Car Monitoring & Control Web System

A real-time web-based system for monitoring and controlling multiple autonomous cars built with Flask, WebSocket (Socket.IO), and vanilla HTML/CSS/JavaScript.

## 🚗 Features

- **Real-time Telemetry**: Live updates of speed, battery, temperature, GPS location
- **Multi-Car Support**: Monitor up to 5 cars simultaneously
- **Interactive Map**: Track car location and set destinations via Leaflet maps
- **Live Camera Feed**: 240p MJPEG stream from car camera
- **Trip History**: Automatic trip logging with distance calculation and route visualization
- **Alerts System**: Browser notifications for critical events (crash detection, low battery)
- **2-Way Communication**: Send commands to car (emergency stop, destination, mode change)
- **Historical Graphs**: Speed and battery history visualization

## 📁 Project Structure

```
mesba7/
├── backend/                   # Raspberry Pi Flask Backend
│   ├── app.py                # Main Flask application
│   ├── state_manager.py      # Car state management
│   ├── serial_handler.py     # Arduino/ESP32 communication
│   ├── camera.py             # MJPEG camera streaming
│   ├── trip_logger.py        # Trip recording and history
│   ├── config.json           # Configuration file
│   ├── trips.json            # Trip history database
│   └── requirements.txt      # Python dependencies
│
└── frontend/                  # Web Application
    ├── index.html            # Car selection page
    ├── dashboard.html        # Main telemetry dashboard
    ├── map.html              # Live map tracking
    ├── camera.html           # Camera stream viewer
    ├── history.html          # Trip history
    ├── alerts.html           # Alerts & notifications
    ├── css/
    │   └── style.css         # Main stylesheet
    └── js/
        ├── socket-client.js  # WebSocket client
        ├── dashboard.js      # Dashboard logic
        ├── map.js            # Map integration
        └── notifications.js  # Browser notifications
```

## 🛠️ Technology Stack

**Backend (Raspberry Pi 5)**:
- Python 3.x
- Flask & Flask-SocketIO
- PySerial (Arduino communication)
- OpenCV (camera streaming)
- Eventlet (async support)

**Frontend**:
- HTML5, CSS3, Vanilla JavaScript
- Socket.IO client
- Leaflet.js (maps)
- Chart.js (graphs)
- Browser Notification API

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi 5 with Ubuntu 24
- Python 3.8+
- Arduino/ESP32 with sensors
- USB camera (or use mock mode for testing)

### Backend Setup (Raspberry Pi)

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Install Python dependencies**:
```bash
pip3 install -r requirements.txt
```

3. **Configure settings** (edit `config.json`):
```json
{
  "serial_port": "/dev/ttyUSB0",
  "serial_baudrate": 115200,
  "camera_index": 0,
  "camera_resolution": [320, 240],
  "car_ids": ["CAR_001", "CAR_002", "CAR_003", "CAR_004", "CAR_005"]
}
```

4. **Run the server**:
```bash
python3 app.py
```

The server will start on `http://0.0.0.0:5000`

### Frontend Setup

1. **Find your Pi's IP address**:
```bash
hostname -I
```

2. **Update SERVER_URL in frontend JavaScript files**:
   - Edit `frontend/js/socket-client.js`
   - Change `const SERVER_URL = 'http://localhost:5000';` to your Pi's IP
   - Example: `const SERVER_URL = 'http://192.168.1.100:5000';`

3. **Open in browser**:
   - Navigate to `frontend/index.html`
   - Select a car
   - Start monitoring!

## 🧪 Testing with Mock Data

The backend includes mock handlers for testing without hardware:

In `backend/app.py`, set:
```python
USE_MOCK = True  # Uses mock serial data and camera
```

This generates simulated telemetry data for 3 cars.

## 📡 Arduino/ESP32 Communication

### Expected Serial Format

The Arduino/ESP32 should send JSON messages via serial (115200 baud):

```json
{
  "car_id": "CAR_001",
  "speed": 45,
  "battery": 85,
  "temperature": 32,
  "gps": {
    "lat": 30.0444,
    "lon": 31.2357
  },
  "crash": false,
  "mode": "auto"
}
```

### Receiving Commands from Pi

The Pi sends commands in JSON format:

```json
{
  "car_id": "CAR_001",
  "command": "set_destination",
  "lat": 30.0555,
  "lon": 31.2468
}
```

Command types:
- `set_destination`: Navigate to coordinates
- `emergency_stop`: Immediate stop
- `change_mode`: Switch between manual/auto

## 🌐 Deployment Options

### Phase 1: Local Network

1. Run backend on Raspberry Pi
2. Connect laptop/phone to same WiFi
3. Access via Pi's local IP: `http://192.168.1.X:5000`

### Phase 2: Cloud Deployment

1. Deploy backend to cloud server (DigitalOcean, AWS, etc.)
2. Configure Pi to connect to cloud server
3. Update frontend `SERVER_URL` to cloud server address
4. Add SSL/HTTPS for secure communication

## 📊 Features Guide

### Dashboard
- Real-time speed gauge
- Battery percentage bar
- Temperature display
- Car status indicator
- Emergency stop button
- Historical speed/battery graphs

### Map
- Live car position tracking
- Path visualization
- Click-to-set destination
- OpenStreetMap integration

### Camera
- Live MJPEG stream (240p)
- Low latency for local network
- Connection status indicator

### Trip History
- Automatic trip recording
- Distance calculation (Haversine formula)
- Duration tracking
- Battery consumption
- Route visualization on map

### Alerts
- Browser notifications for critical events
- Crash detection alerts
- Low battery warnings
- High temperature warnings

## ⚙️ Configuration

### Changing Number of Cars

Edit `backend/config.json`:
```json
{
  "car_ids": ["CAR_001", "CAR_002", "CAR_003"]
}
```

### Changing Camera Resolution

Edit `backend/config.json`:
```json
{
  "camera_resolution": [640, 480]  // Increase for better quality
}
```

### Changing Telemetry Update Rate

Edit `backend/config.json`:
```json
{
  "telemetry_interval": 0.5  // Update every 0.5 seconds
}
```

## 🐛 Troubleshooting

### Backend won't start:
- Check if port 5000 is already in use
- Verify Python dependencies are installed
- Check serial port permissions: `sudo chmod 666 /dev/ttyUSB0`

### Camera not working:
- Test camera: `ls /dev/video*`
- Check camera index in config.json
- Use mock mode for testing without camera

### Frontend can't connect:
- Verify backend is running
- Check SERVER_URL in JavaScript files
- Ensure firewall allows port 5000
- Check CORS settings in Flask app

### Serial communication issues:
- Verify Arduino is sending correct JSON format
- Check baud rate matches (115200)
- Test with mock mode first
- Check serial port permissions

## 📝 Future Enhancements

- [ ] Add database (PostgreSQL/MongoDB) instead of JSON files
- [ ] User authentication and multi-user support
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Fleet management features
- [ ] Replay trip animations
- [ ] Export trip data (CSV, GPX)

## 📄 License

This is a graduation project. Feel free to use and modify for educational purposes.

## 👨‍💻 Development

Built as a graduation project for autonomous vehicle monitoring and control.

**Author**: Student Project  
**Year**: 2026

---

Made with ❤️ for autonomous vehicles 🚗
