import cv2
import mediapipe as mp
import numpy as np

class VisionProcessor:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=0, 
            min_detection_confidence=0.5  # Lowered for better detection
        )
        self.tracking_enabled = False
        self.center_tolerance = 0.15

    def enable_tracking(self, enabled: bool):
        self.tracking_enabled = enabled

    def process_frame(self, frame):
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = self.face_detection.process(rgb_frame)
        
        target = None

        # Draw center crosshair
        cv2.line(frame, (w // 2, 0), (w // 2, h), (50, 50, 50), 1)
        cv2.line(frame, (0, h // 2), (w, h // 2), (50, 50, 50), 1)

        # Draw the "center zone" rectangle (where the face needs to be)
        tol_x = int(w * self.center_tolerance)
        tol_y = int(h * self.center_tolerance)
        zone_x1 = w // 2 - tol_x
        zone_y1 = h // 2 - tol_y
        zone_x2 = w // 2 + tol_x
        zone_y2 = h // 2 + tol_y
        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (255, 255, 0), 1)

        if results.detections:
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            
            x = max(0, int(bbox.xmin * w))
            y = max(0, int(bbox.ymin * h))
            face_w = int(bbox.width * w)
            face_h = int(bbox.height * h)
            
            cx = x + face_w // 2
            cy = y + face_h // 2
            score = detection.score[0]

            # Check if centered
            x_off = abs(cx - w // 2) / w
            y_off = abs(cy - h // 2) / h
            centered = (x_off < self.center_tolerance) and (y_off < self.center_tolerance)
            
            # Color: green if centered, red if not
            color = (0, 255, 0) if centered else (0, 0, 255)
            status = "CENTERED" if centered else "ALIGNING..."
            
            cv2.rectangle(frame, (x, y), (x + face_w, y + face_h), color, 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
            cv2.putText(frame, f"{status} | {score*100:.0f}%", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            target = (x, y, x + face_w, y + face_h, cx, cy, face_w, face_h, face_w * face_h, score)
        else:
            cv2.putText(frame, "NO FACE DETECTED", (30, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return frame, target
