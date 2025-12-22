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
        
        # Runtime state
        self.in_zone_count = 0
        self.out_zone_count = 0
        self.current_zone_occupancy = 0
        self.alerts_count = 0
        self.frame_count = 0
        self.tracked_objects = {}
        
        # FPS calculation
        self.fps_start_time = datetime.now()
        self.fps_frame_count = 0
        self.current_fps = 0

    def reset_stats(self):
        """Reset all tracking statistics"""
        self.in_zone_count = 0
        self.out_zone_count = 0
        self.current_zone_occupancy = 0
        self.alerts_count = 0
        self.frame_count = 0
        self.tracked_objects = {}
        self.occupancy_history.clear()
        self.in_history.clear()
        self.out_history.clear()
        print("🔄 Statistics have been reset")

    def process_frame(self, frame, line_points, alert_threshold=10):
        """Process a single frame: Detect, Track, Count, Draw"""
        h, w = frame.shape[:2]
        self.frame_count += 1
        self.fps_frame_count += 1
        
        # Calculate FPS
        if (datetime.now() - self.fps_start_time).total_seconds() >= 1.0:
            self.current_fps = self.fps_frame_count / (datetime.now() - self.fps_start_time).total_seconds()
            self.fps_frame_count = 0
            self.fps_start_time = datetime.now()
            
        # Zone Bounds
        zone_x1, zone_y1 = line_points[0]
        zone_x2, zone_y2 = line_points[1]
        
        # Ensure correct TL/BR order
        min_x = min(zone_x1, zone_x2)
        min_y = min(zone_y1, zone_y2)
        max_x = max(zone_x1, zone_x2)
        max_y = max(zone_y1, zone_y2)
        
        # 1. Draw Zone
        frame = self.draw_counting_zone(frame, (min_x, min_y), (max_x, max_y), 
                                      self.in_zone_count, self.out_zone_count)
        
        # 2. Run YOLO Track
        results = self.model.track(frame, persist=True, classes=[0], 
                                  conf=self.confidence, verbose=False)
        
        boxes_list = []
        ids_list = []
        
        # Track current frame's occupancy for this specific frame
        current_frame_occupants = set()
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.cpu().numpy().astype(int)
            
            for box, track_id in zip(boxes, track_ids):
                boxes_list.append(box)
                ids_list.append(track_id)
                
                x1, y1, x2, y2 = box
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2) 
                
                # Tracking uses bottom-center (feet) for better accuracy in top-down view
                feet_y = int(y2)
                feet_x = int(cx)
                
                # Check if inside zone
                is_inside = (min_x <= feet_x <= max_x) and (min_y <= feet_y <= max_y)
                
                if is_inside:
                    current_frame_occupants.add(track_id)
                
                # State Logic
                if track_id not in self.tracked_objects:
                    # New object
                    self.tracked_objects[track_id] = is_inside
                else:
                    was_inside = self.tracked_objects[track_id]
                    
                    if not was_inside and is_inside:
                        self.in_zone_count += 1 # ENTERED ZONE
                    elif was_inside and not is_inside:
                        self.out_zone_count += 1 # EXITED ZONE
                    
                    self.tracked_objects[track_id] = is_inside
        
        # 3. Draw Detections
        if boxes_list:
            frame = self.draw_detections(frame, boxes_list, ids_list) # Keep this or modify to highlight inside?
            
        # 4. Update Statistics
        self.current_zone_occupancy = len(current_frame_occupants)
        self.occupancy_history.append(self.current_zone_occupancy)
        
        if self.current_zone_occupancy >= alert_threshold:
            self.alerts_count += 1
        
        # 5. Draw Dashboard
        frame = self.create_dashboard(frame, self.in_zone_count, self.out_zone_count, 
                                    self.current_zone_occupancy, self.frame_count, 
                                    self.alerts_count, self.current_fps)
        
        # 6. Draw Alert Overlay
        if self.current_zone_occupancy >= alert_threshold:
            cv2.putText(frame, "! OVERCROWDING ALERT !", (w//2 - 150, 100),
                       cv2.FONT_HERSHEY_DUPLEX, 0.8, self.colors['danger'], 2)
                       
        return frame
    
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
        print("="*60)
        print("Instructions:")
        print("  1. Click TWO points to define the RECTANGLE ZONE")
        print("  2. First click = Top-Left Corner")
        print("  3. Second click = Bottom-Right Corner")
        print("  4. Press 'ENTER' when done to continue")
        print("  5. Press 'R' to reset and start over")
        print("  6. Press 'ESC' to cancel")
        print("="*60 + "\n")
        
        window_name = "Setup Counting Zone - Click TL and BR"
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
                    instruction = "Click TL Corner"
                    cv2.putText(display_frame, instruction, (20, 35),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                elif len(self.line_points) == 1:
                    instruction = "Click BR Corner"
                    cv2.putText(display_frame, instruction, (20, 35),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                instruction = "Zone configured! Press ENTER"
                cv2.putText(display_frame, instruction, (20, 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Draw the points and zone
            if len(self.line_points) >= 1:
                cv2.circle(display_frame, tuple(self.line_points[0]), 8, (0, 255, 0), -1)
                cv2.putText(display_frame, "TL", 
                           (self.line_points[0][0] + 10, self.line_points[0][1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            if len(self.line_points) == 2:
                cv2.rectangle(display_frame, tuple(self.line_points[0]), 
                             tuple(self.line_points[1]), (0, 255, 0), 2)
                cv2.circle(display_frame, tuple(self.line_points[1]), 8, (0, 0, 255), -1)
                cv2.putText(display_frame, "BR", 
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
        """Create professional dashboard overlay (Ultra-Compact Version)"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        
        # Bottom panel (Ultra-Compact)
        panel_height = 60
        cv2.rectangle(overlay, (0, h - panel_height), (w, h), self.colors['dark'], -1)
        
        # Metric cards
        card_width = w // 2 - 15
        card_height = 40
        card_y = h - panel_height + 10
        
        self._draw_metric_card(overlay, 10, card_y, card_width, card_height,
                              "OUT", str(out_count), self.colors['info'], "")
        
        color = self.colors['danger'] if current_occupancy >= 10 else self.colors['primary']
        self._draw_metric_card(overlay, card_width + 20, card_y, card_width, card_height,
                              "NOW", str(current_occupancy), color, "")
        
        # Top Info (Transparent, just text)
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(overlay, f"RPI MONITOR | FPS: {fps:.1f} | {timestamp}", 
                   (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.colors['light'], 1)
        
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        return frame
    
    def _draw_metric_card(self, frame, x, y, width, height, label, value, color, icon):
        """Draw individual metric card (Ultra-Compact)"""
        cv2.rectangle(frame, (x, y), (x + width, y + height), (60, 60, 60), -1)
        cv2.rectangle(frame, (x, y), (x + width, y + height), color, 1)
        
        # Value (Large)
        cv2.putText(frame, value, (x + 10, y + 28), 
                   cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
        # Label (Small, below value)
        cv2.putText(frame, label, (x + 10, y + height - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)
    
    def draw_counting_zone(self, frame, tl, br, in_count, out_count):
        """Draw counting zone rectangle"""
        cv2.rectangle(frame, tl, br, self.colors['accent'], 3)
        
        # Calculate label positions
        mid_x = (tl[0] + br[0]) // 2
        min_y = min(tl[1], br[1])
        max_y = max(tl[1], br[1])
        
        
        # In Label (Top) - Disabled

        
        # Out Label (Bottom)
        cv2.putText(frame, f"OUT: {out_count}", (tl[0], max_y + 15),
                   cv2.FONT_HERSHEY_DUPLEX, 0.5, self.colors['info'], 1)
        
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
            cv2.rectangle(frame, (int(x1), int(y1) - 15), (int(x1) + 60, int(y1)), 
                         self.colors['primary'], -1)
            cv2.putText(frame, label, (int(x1) + 2, int(y1) - 3),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
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
                
                frame = self.process_frame(frame, line_points, alert_threshold)
                
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
        line_points = monitor.setup_counting_zone(camera)
        camera.release()
        
        if line_points is None:
            print("Setup cancelled. Exiting...")
            return
    elif args.line_start and args.line_end:
        line_points = [args.line_start, args.line_end]
    else:
        # Default Zone (Central Rectangle)
        line_points = [[100, 100], [540, 380]]
    
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
