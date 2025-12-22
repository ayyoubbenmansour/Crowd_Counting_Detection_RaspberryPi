from flask import Flask, render_template, Response, request, redirect, url_for, send_from_directory
import os
import cv2
import time
from werkzeug.utils import secure_filename
from crowd_counting_rpi import ProfessionalHallwayMonitor, RaspberryPiCameraWrapper

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max upload

import json
from datetime import datetime

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Logging Helper Functions
LOG_FILE = 'logs.json'

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_log(title, out_count):
    logs = load_logs()
    entry = {
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'title': title,
        'out_count': out_count
    }
    logs.append(entry)
    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=4)


# Global Constants
# Initial default, will be updated by the camera stream
CAMERA_RESOLUTION = [640, 480]
CURRENT_PERCENTAGE = 0.85
ALERT_THRESHOLD = 10 # Default threshold

def calculate_zone_from_percentage(percentage, w=None, h=None):
    """Calculate centered zone coordinates based on percentage (0.1 to 1.0)"""
    if w is None or h is None:
        w, h = CAMERA_RESOLUTION
        
    # Ensure percentage is clamped
    percentage = max(0.1, min(1.0, float(percentage)))
    
    # Calculate box dimensions
    box_w = int(w * percentage)
    box_h = int(h * percentage)
    
    # Calculate top-left position to center it
    x1 = (w - box_w) // 2
    y1 = (h - box_h) // 2
    
    x2 = x1 + box_w
    y2 = y1 + box_h
    
    return [[x1, y1], [x2, y2]]

# Global Monitor Instance
monitor = ProfessionalHallwayMonitor()
# Default Zone - Central Rectangle [Top-Left, Bottom-Right]
# Will be overwritten if using interactive setup or config
line_points = [[50, 50], [590, 430]] 

# Video Streaming Generator
def generate_frames(source=0, title=None):
    global line_points, CAMERA_RESOLUTION, ALERT_THRESHOLD, monitor
    
    # Determine which monitor instance to use
    if source == 0:
        # LIVE FEED: Use the global persistent monitor
        current_monitor = monitor
    else:
        # UPLOADED VIDEO: Create a FRESH, ISOLATED monitor instance
        # This ensures stats (In/Out/People) start from ZERO for every new video
        current_monitor = ProfessionalHallwayMonitor()
    
    # Use RaspberryPiCameraWrapper if source is 0 (default camera)
    if source == 0:
        try:
            # Try to use Picamera2 first, fallback to OpenCV if not on Pi/not available
            # Note: We pass use_picamera2=True, the wrapper handles availability check
            camera = RaspberryPiCameraWrapper(use_picamera2=True, resolution=tuple(CAMERA_RESOLUTION))
        except Exception as e:
            print(f"⚠️ Camera init failed: {e}. Falling back to standard OpenCV.")
            camera = cv2.VideoCapture(source)
    else:
        # File path source
        camera = cv2.VideoCapture(source)
    
    # Initialize resolution from THIS stream (Camera or Upload)
    current_line_points = line_points # Default fallback
    
    # Determine if we are using the wrapper or standard cv2
    is_wrapper = hasattr(camera, 'use_picamera2')
    is_opened = camera.isOpened() if not is_wrapper else True # Wrapper might not have isOpened or logic differs
    
    if is_opened:
        width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width > 0 and height > 0:
            # Recalculate zone specifically for this stream size
            # This ensures uploaded videos get a zone proportional to THEIR size
            current_line_points = calculate_zone_from_percentage(CURRENT_PERCENTAGE, width, height)
            print(f"✅ Stream resolution: {width}x{height} - Zone Recalculated")
            
    try:
        while True:
            success, frame = camera.read()
            if not success:
                break
            
            # Process frame using the SELECTED monitor (Global or Local)
            # Use local current_line_points instead of global line_points
            processed_frame = current_monitor.process_frame(frame, current_line_points, alert_threshold=ALERT_THRESHOLD)
            
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        # When stream ends (or is stopped), save log if it was an uploaded video
        if source != 0 and title:
            print(f"📝 Logging stats for {title}: OUT={current_monitor.out_zone_count}")
            save_log(title, current_monitor.out_zone_count)
            
        camera.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(0), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Reset statistics for the new video -- NOW HANDLED BY FRESH INSTANCE in generate_frames
            # monitor.reset_stats()
            
            return render_template('upload.html', filename=filename)
    return render_template('upload.html')

@app.route('/upload_feed/<filename>')
def upload_feed(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    # Pass filename as title for logging
    return Response(generate_frames(filepath, title=filename), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logs')
def view_logs():
    logs_data = load_logs()
    return render_template('logs.html', logs=logs_data)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    global line_points, CURRENT_PERCENTAGE, ALERT_THRESHOLD
    
    if request.method == 'POST':
        try:
            # Update Zone Percentage
            percentage = float(request.form.get('zone_percentage', CURRENT_PERCENTAGE))
            line_points = calculate_zone_from_percentage(percentage)
            CURRENT_PERCENTAGE = percentage
            
            # Update Threshold
            threshold_val = int(request.form.get('alert_threshold', ALERT_THRESHOLD))
            ALERT_THRESHOLD = threshold_val
            
            return render_template('settings.html', success=True, percentage=CURRENT_PERCENTAGE, threshold=ALERT_THRESHOLD)
        except ValueError:
            pass
            
    return render_template('settings.html', percentage=CURRENT_PERCENTAGE, threshold=ALERT_THRESHOLD)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
