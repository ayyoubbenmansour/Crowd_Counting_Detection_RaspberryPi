"""
Raspberry Pi Camera Integration for Hallway Monitor
Supports both picamera2 and standard camera indices
"""

from ultralytics import YOLO
import cv2
import numpy as np
import argparse
from datetime import datetime
from collections import deque

# Try to import picamera2
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("⚠️  picamera2 not available. Using OpenCV VideoCapture instead.")

class RaspberryPiCameraWrapper:
    """Wrapper to handle both picamera2 and OpenCV capture"""
    def __init__(self, use_picamera2=True, resolution=(640, 480), framerate=30):
        self.use_picamera2 = use_picamera2 and PICAMERA2_AVAILABLE
        
        if self.use_picamera2:
            print("🎥 Initializing Raspberry Pi Camera (picamera2)...")
            self.picam2 = Picamera2()
            config = self.picam2.create_preview_configuration(
                main={"size": resolution, "format": "RGB888"}
            )
            self.picam2.configure(config)
            self.picam2.start()
            print("✅ Raspberry Pi Camera initialized successfully!")
            self.width, self.height = resolution
            self.fps = framerate
        else:
            print("🎥 Initializing camera via OpenCV...")
            # Try different camera indices for Raspberry Pi
            for idx in [0, 1, 2]:
                self.cap = cv2.VideoCapture(idx)
                if self.cap.isOpened():
                    print(f"✅ Camera found at index {idx}")
                    self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
                    break
            else:
                raise RuntimeError("❌ Could not open camera!")
    
    def read(self):
        """Read a frame from the camera"""
        if self.use_picamera2:
            frame = self.picam2.capture_array()
            # picamera2 returns RGB, OpenCV expects BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return True, frame
        else:
            return self.cap.read()
    
    def isOpened(self):
        """Check if camera is opened"""
        if self.use_picamera2:
            return True  # picam2 doesn't have isOpened, assume true after init
        else:
            return self.cap.isOpened()
    
    def get(self, prop):
        """Get camera property"""
        if self.use_picamera2:
            if prop == cv2.CAP_PROP_FRAME_WIDTH:
                return self.width
            elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
                return self.height
            elif prop == cv2.CAP_PROP_FPS:
                return self.fps
            return 0
        else:
            return self.cap.get(prop)
    
    def release(self):
        """Release the camera"""
        if self.use_picamera2:
            self.picam2.stop()
            print("🛑 Raspberry Pi Camera stopped")
        else:
            self.cap.release()
            print("🛑 Camera released")


class ProfessionalHallwayMonitor:
    def __init__(self, model_path="yolo11n.pt", confidence=0.5):
        """Initialize the hallway monitoring system"""
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.video_writer = None
        
        # Line setup variables
        self.line_points = []
        self.setup_complete = False
        
        # Enhanced UI colors (BGR format)
        self.colors = {
            'primary': (255, 140, 0),      # Deep Sky Blue
            'success': (0, 255, 0),         # Green
            'danger': (0, 0, 255),          # Red
            'warning': (0, 165, 255),       # Orange
            'info': (255, 200, 0),          # Cyan
            'dark': (40, 40, 40),           # Dark background
            'light': (240, 240, 240),       # Light text
            'accent': (255, 0, 255),        # Magenta
        }
        
        # Statistics tracking
        self.history_length = 100
        self.occupancy_history = deque(maxlen=self.history_length)
        self.in_history = deque(maxlen=self.history_length)
        self.out_history = deque(maxlen=self.history_length)
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse clicks for line setup"""
        if event == cv2.EVENT_LBUTTONDOWN and not self.setup_complete:
            if len(self.line_points) == 0:
                self.line_points.append([x, y])
                print(f"✓ First point set at ({x}, {y})")
            elif len(self.line_points) == 1:
                self.line_points.append([x, y])
                self.setup_complete = True
                print(f"✓ Second point set at ({x}, {y})")
                print(f"✓ Counting line configured: {self.line_points}")
    
    def setup_counting_line(self, camera):
        """Interactive line setup mode with Raspberry Pi camera"""
        print("\n" + "="*60)
        print("🎯 INTERACTIVE LINE SETUP MODE")
        print("="*60)
        print("Instructions:")
        print("  1. Click TWO points to draw the counting line")
        print("  2. First click = Line start point")
        print("  3. Second click = Line end point")
        print("  4. Press 'ENTER' when done to continue")
        print("  5. Press 'R' to reset and start over")
        print("  6. Press 'ESC' to cancel")
        print("="*60 + "\n")
        
        window_name = "Setup Counting Line - Click 2 Points"
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        
        while True:
            ret, frame = camera.read()
            if not ret:
                print("Error: Could not read frame")
                cv2.destroyWindow(window_name)
                return None
            
            h, w = frame.shape[:2]
            display_frame = frame.copy()
            
            # Draw instructions overlay
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 60), (40, 40, 40), -1)
            cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)
            
            if not self.setup_complete:
                if len(self.line_points) == 0:
                    instruction = "Click FIRST point for line start"
                    cv2.putText(display_frame, instruction, (20, 35),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                elif len(self.line_points) == 1:
                    instruction = "Click SECOND point for line end"
                    cv2.putText(display_frame, instruction, (20, 35),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                instruction = "Line configured! Press ENTER to continue"
                cv2.putText(display_frame, instruction, (20, 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Draw the points and line
            if len(self.line_points) >= 1:
                cv2.circle(display_frame, tuple(self.line_points[0]), 8, (0, 255, 0), -1)
                cv2.putText(display_frame, f"Start: {self.line_points[0]}", 
                           (self.line_points[0][0] + 10, self.line_points[0][1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            if len(self.line_points) == 2:
                cv2.line(display_frame, tuple(self.line_points[0]), 
                        tuple(self.line_points[1]), (0, 255, 255), 3)
                cv2.circle(display_frame, tuple(self.line_points[1]), 8, (0, 0, 255), -1)
                cv2.putText(display_frame, f"End: {self.line_points[1]}", 
                           (self.line_points[1][0] + 10, self.line_points[1][1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            
            cv2.imshow(window_name, display_frame)
            
            key = cv2.waitKey(30) & 0xFF
            
            if key == ord('r') or key == ord('R'):
                self.line_points = []
                self.setup_complete = False
                print("↻ Reset - Click two points again")
            elif key == 27:
                print("✗ Setup cancelled")
                cv2.destroyWindow(window_name)
                return None
            elif key == 13 and self.setup_complete:
                break
        
        cv2.destroyWindow(window_name)
        return self.line_points
    
    def create_dashboard(self, frame, in_count, out_count, current_occupancy, 
                        frame_count, alerts_count, fps=0):
        """Create professional dashboard overlay"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # Top bar
        cv2.rectangle(overlay, (0, 0), (w, 80), self.colors['dark'], -1)
        cv2.putText(overlay, "RASPBERRY PI HALLWAY MONITOR", 
                   (20, 35), cv2.FONT_HERSHEY_DUPLEX, 1.0, self.colors['primary'], 2)
        cv2.putText(overlay, f"AI Detection | FPS: {fps:.1f}", 
                   (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors['light'], 1)
        
        # Bottom panel
        panel_height = 200
        cv2.rectangle(overlay, (0, h - panel_height), (w, h), self.colors['dark'], -1)
        
        # Metric cards
        card_width = w // 4 - 20
        card_height = 140
        card_y = h - panel_height + 20
        
        self._draw_metric_card(overlay, 10, card_y, card_width, card_height,
                              "ENTERED", str(in_count), self.colors['success'], "IN")
        self._draw_metric_card(overlay, card_width + 20, card_y, card_width, card_height,
                              "EXITED", str(out_count), self.colors['info'], "OUT")
        
        color = self.colors['danger'] if current_occupancy >= 10 else self.colors['primary']
        self._draw_metric_card(overlay, 2 * (card_width + 10) + 10, card_y, card_width, card_height,
                              "OCCUPANCY", str(current_occupancy), color, "NOW")
        self._draw_metric_card(overlay, 3 * (card_width + 10) + 10, card_y, card_width, card_height,
                              "ALERTS", str(alerts_count), self.colors['warning'], "!")
        
        # Status
        status_x = w - 180
        status_y = h - 50
        if current_occupancy >= 15:
            status_text = "CRITICAL"
            status_color = self.colors['danger']
        elif current_occupancy >= 10:
            status_text = "WARNING"
            status_color = self.colors['warning']
        else:
            status_text = "NORMAL"
            status_color = self.colors['success']
        
        cv2.rectangle(overlay, (status_x, status_y), (status_x + 160, status_y + 35), 
                     status_color, -1)
        cv2.putText(overlay, f"STATUS: {status_text}", (status_x + 10, status_y + 23),
                   cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 2)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(overlay, timestamp, (w - 250, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.colors['light'], 1)
        
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        return frame
    
    def _draw_metric_card(self, frame, x, y, width, height, label, value, color, icon):
        """Draw individual metric card"""
        cv2.rectangle(frame, (x, y), (x + width, y + height), (60, 60, 60), -1)
        cv2.rectangle(frame, (x, y), (x + width, y + height), color, 3)
        cv2.rectangle(frame, (x, y), (x + width, y + 8), color, -1)
        cv2.putText(frame, icon, (x + 15, y + 55), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)
        cv2.putText(frame, value, (x + 70, y + 60), 
                   cv2.FONT_HERSHEY_DUPLEX, 1.8, (255, 255, 255), 3)
        cv2.putText(frame, label, (x + 15, y + height - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    
    def draw_counting_line(self, frame, line_points, in_count, out_count):
        """Draw counting line"""
        cv2.line(frame, tuple(line_points[0]), tuple(line_points[1]), 
                (255, 255, 255), 6)
        cv2.line(frame, tuple(line_points[0]), tuple(line_points[1]), 
                self.colors['accent'], 3)
        
        mid_x = (line_points[0][0] + line_points[1][0]) // 2
        mid_y = (line_points[0][1] + line_points[1][1]) // 2
        
        cv2.arrowedLine(frame, (mid_x - 60, mid_y - 40), (mid_x - 60, mid_y - 10),
                       self.colors['success'], 3, tipLength=0.4)
        cv2.putText(frame, f"IN: {in_count}", (mid_x - 100, mid_y - 50),
                   cv2.FONT_HERSHEY_DUPLEX, 0.6, self.colors['success'], 2)
        
        cv2.arrowedLine(frame, (mid_x + 60, mid_y + 10), (mid_x + 60, mid_y + 40),
                       self.colors['info'], 3, tipLength=0.4)
        cv2.putText(frame, f"OUT: {out_count}", (mid_x + 40, mid_y + 60),
                   cv2.FONT_HERSHEY_DUPLEX, 0.6, self.colors['info'], 2)
        
        return frame
    
    def draw_detections(self, frame, boxes, track_ids):
        """Draw detection boxes"""
        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = box
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), 
                         self.colors['primary'], 3)
            cv2.circle(frame, (cx, cy), 8, (255, 255, 255), -1)
            cv2.circle(frame, (cx, cy), 5, self.colors['primary'], -1)
            
            label = f"ID:{track_id}"
            cv2.rectangle(frame, (int(x1), int(y1) - 25), (int(x1) + 80, int(y1)), 
                         self.colors['primary'], -1)
            cv2.putText(frame, label, (int(x1) + 5, int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def monitor_with_rpi_camera(self, line_points, use_picamera2=True, 
                                resolution=(640, 480), output_path=None,
                                show_display=True, alert_threshold=10):
        """Monitor using Raspberry Pi camera"""
        camera = RaspberryPiCameraWrapper(use_picamera2, resolution)
        
        w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps_cap = int(camera.get(cv2.CAP_PROP_FPS))
        
        if output_path:
            self.video_writer = cv2.VideoWriter(
                output_path,
                cv2.VideoWriter_fourcc(*'mp4v'),
                fps_cap if fps_cap > 0 else 30,
                (w, h)
            )
        
        in_count = 0
        out_count = 0
        tracked_objects = {}
        line_y = line_points[0][1]
        alerts_count = 0
        frame_count = 0
        
        fps_start_time = datetime.now()
        fps_frame_count = 0
        current_fps = 0
        
        print("\n" + "="*60)
        print("🚀 RASPBERRY PI HALLWAY MONITOR ACTIVE")
        print("="*60)
        print("📹 Press 'Q' to quit")
        print("="*60 + "\n")
        
        try:
            while camera.isOpened():
                success, frame = camera.read()
                if not success:
                    break
                
                frame_count += 1
                fps_frame_count += 1
                
                if (datetime.now() - fps_start_time).total_seconds() >= 1.0:
                    current_fps = fps_frame_count / (datetime.now() - fps_start_time).total_seconds()
                    fps_frame_count = 0
                    fps_start_time = datetime.now()
                
                frame = self.draw_counting_line(frame, line_points, in_count, out_count)
                
                results = self.model.track(frame, persist=True, classes=[0], 
                                          conf=self.confidence, verbose=False)
                
                boxes_list = []
                ids_list = []
                
                if results[0].boxes.id is not None:
                    boxes = results[0].boxes.xyxy.cpu().numpy()
                    track_ids = results[0].boxes.id.cpu().numpy().astype(int)
                    
                    for box, track_id in zip(boxes, track_ids):
                        boxes_list.append(box)
                        ids_list.append(track_id)
                        
                        x1, y1, x2, y2 = box
                        cx = int((x1 + x2) / 2)
                        cy = int((y1 + y2) / 2)
                        
                        if track_id not in tracked_objects:
                            tracked_objects[track_id] = cy
                        else:
                            prev_y = tracked_objects[track_id]
                            
                            if prev_y < line_y <= cy:
                                in_count += 1
                            elif prev_y > line_y >= cy:
                                out_count += 1
                            
                            tracked_objects[track_id] = cy
                
                if boxes_list:
                    frame = self.draw_detections(frame, boxes_list, ids_list)
                
                current_occupancy = in_count - out_count
                self.occupancy_history.append(current_occupancy)
                
                if current_occupancy >= alert_threshold:
                    alerts_count += 1
                
                frame = self.create_dashboard(frame, in_count, out_count, current_occupancy,
                                            frame_count, alerts_count, current_fps)
                
                if current_occupancy >= alert_threshold:
                    cv2.putText(frame, "! OVERCROWDING ALERT !", (w//2 - 200, 120),
                               cv2.FONT_HERSHEY_DUPLEX, 1.2, self.colors['danger'], 3)
                
                if self.video_writer:
                    self.video_writer.write(frame)
                
                if show_display:
                    cv2.imshow("Raspberry Pi Hallway Monitor", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == ord('Q'):
                        break
        
        finally:
            camera.release()
            if self.video_writer:
                self.video_writer.release()
            cv2.destroyAllWindows()
        
        print("\n" + "="*60)
        print("📊 MONITORING SESSION COMPLETE")
        print("="*60)
        print(f"✅ Total frames: {frame_count}")
        print(f"📥 Entered: {in_count}")
        print(f"📤 Exited: {out_count}")
        print(f"👥 Final occupancy: {current_occupancy}")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Raspberry Pi Hallway Monitor")
    parser.add_argument('--model', type=str, default='yolo11n.pt',
                       help='YOLO model path')
    parser.add_argument('--output', type=str, default=None,
                       help='Output video path')
    parser.add_argument('--threshold', type=int, default=10,
                       help='Alert threshold')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive line setup')
    parser.add_argument('--line-start', nargs=2, type=int, default=None,
                       help='Line start (x y)')
    parser.add_argument('--line-end', nargs=2, type=int, default=None,
                       help='Line end (x y)')
    parser.add_argument('--resolution', nargs=2, type=int, default=[640, 480],
                       help='Camera resolution (width height)')
    parser.add_argument('--use-opencv', action='store_true',
                       help='Use OpenCV instead of picamera2')
    parser.add_argument('--no-display', action='store_true',
                       help='Headless mode')
    
    args = parser.parse_args()
    
    monitor = ProfessionalHallwayMonitor(model_path=args.model, confidence=0.5)
    
    # Initialize camera for line setup if needed
    if args.interactive:
        camera = RaspberryPiCameraWrapper(
            use_picamera2=not args.use_opencv,
            resolution=tuple(args.resolution)
        )
        line_points = monitor.setup_counting_line(camera)
        camera.release()
        
        if line_points is None:
            print("Setup cancelled. Exiting...")
            return
    elif args.line_start and args.line_end:
        line_points = [args.line_start, args.line_end]
    else:
        # Default line
        line_points = [[100, 240], [540, 240]]
    
    # Start monitoring
    monitor.monitor_with_rpi_camera(
        line_points=line_points,
        use_picamera2=not args.use_opencv,
        resolution=tuple(args.resolution),
        output_path=args.output,
        show_display=not args.no_display,
        alert_threshold=args.threshold
    )


if __name__ == "__main__":
    main()
