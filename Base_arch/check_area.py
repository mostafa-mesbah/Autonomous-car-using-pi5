from flask import Flask, Response
from ultralytics import YOLO
import cv2

app = Flask(__name__)

# Load model once
model = YOLO("/home/uav/clone/Autonomous-car-using-pi5/Base_arch/fils/best_traffic_signs.pt")

# Open camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open camera")


def generate_frames():
    while True:

        success, frame = cap.read()

        if not success:
            break

        results = model(frame, verbose=False)

        for result in results:

            for box in result.boxes:

                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)

                width = x2 - x1
                height = y2 - y1

                area = width * height

                conf = float(box.conf[0])
                cls = int(box.cls[0])

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                label = (
                    f"Class:{cls} "
                    f"Conf:{conf:.2f} "
                    f"Area:{int(area)}"
                )

                cv2.putText(
                    frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

        ret, buffer = cv2.imencode('.jpg', frame)

        frame_bytes = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame_bytes +
            b'\r\n'
        )


@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>YOLO Stream</title>
        </head>
        <body>
            <h2>YOLO Live Detection</h2>
            <img src="/video_feed">
        </body>
    </html>
    """


@app.route('/video_feed')
def video_feed():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True
    )