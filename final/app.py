from flask import Flask, Response, render_template, jsonify
import requests
import cv2
from io import BytesIO
from PIL import Image
import numpy as np
from tensorflow.keras.models import load_model
import os

# Load the trained model
model_path = os.path.join('models', '3cls.h5')
new_model = load_model(model_path)

# Class labels
#arr = {0: "Explosion", 1: "Fighting", 2: "Normal", 3: "Shooting", 4: "Vandalism"}
arr={0: "Explosion", 1: "Normal", 2: "Shooting"}

# ESP32-CAM stream URLs
stream_urls = {
    "cam1": "http://192.168.188.227/1280x720.mjpeg",
    "cam2": "http://192.168.188.240/1280x720.mjpeg",
}

# ESP8266 IP address (same for both servos)
esp8266_ip = "http://192.168.188.41"  # Change to your ESP8266 IP

# Flask app
app = Flask(__name__)

def generate_frames(stream_url):
    """Generate frames from ESP32-CAM stream."""
    try:
        response = requests.get(stream_url, stream=True, timeout=10)
        if response.status_code != 200:
            return
        bytes_data = b""
        for chunk in response.iter_content(chunk_size=1024):
            bytes_data += chunk

            start = bytes_data.find(b'\xff\xd8')
            end = bytes_data.find(b'\xff\xd9')

            if start != -1 and end != -1:
                jpg = bytes_data[start:end + 2]
                bytes_data = bytes_data[end + 2:]

                try:
                    img = Image.open(BytesIO(jpg))
                    frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    if stream_url==stream_urls["cam1"]:
                        # Rotate the frame upside down
                        frame = cv2.rotate(frame, cv2.ROTATE_180)
                    frame_resized = cv2.resize(frame, (256, 256))
                    frame_normalized = frame_resized / 255.0
                    frame_input = np.expand_dims(frame_normalized, axis=0)

                    y = new_model.predict(frame_input, verbose=0)
                    prediction = arr[np.argmax(y)]

                    if prediction in ["Explosion","Shooting"]:
                        cv2.putText(frame, prediction, (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 7)
                    else:                        
                        cv2.putText(frame, prediction, (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)

                    _, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()

                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                except Exception as e:
                    print(f"Error processing frame: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Could not connect to the stream: {e}")

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html', cameras=stream_urls.keys())

@app.route('/video_feed/<cam_id>')
def video_feed(cam_id):
    """Video streaming route for a specific camera."""
    stream_url = stream_urls.get(cam_id)
    if not stream_url:
        return "Camera not found", 404
    return Response(generate_frames(stream_url), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control_servo/<servo_id>/<direction>')
def control_servo(servo_id, direction):
    """Send request to ESP8266 to control the specified servo."""
    if servo_id not in ["servo1", "servo2"]:
        return jsonify({"error": "Invalid servo ID"}), 400

    commands = {
        "left": f"/{servo_id}/left",
        "right": f"/{servo_id}/right",
        "stop": f"/{servo_id}/stop"
    }

    if direction in commands:
        requests.get(f"{esp8266_ip}{commands[direction]}")
        return jsonify({"message": f"{servo_id} moved {direction}"}), 200
    else:
        return jsonify({"error": "Invalid direction"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
