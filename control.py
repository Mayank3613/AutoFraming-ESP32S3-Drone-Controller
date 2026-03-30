import time

class VisualServoController:
    """
    Proportional visual servo controller for drone attendance.
    
    Instead of binary LEFT/RIGHT, outputs RC stick values (1000-2000):
      - 1500 = center/neutral
      - <1500 = left/down/backward
      - >1500 = right/up/forward
    
    The further the face is from center, the stronger the correction.
    """

    def __init__(self):
        self.center_tolerance = 0.15  # 15% of frame = "centered"
        
        # Proportional gains (how aggressively to correct)
        self.roll_gain = 300     # max deviation from 1500 for roll
        self.throttle_gain = 250 # max deviation from 1500 for throttle
        self.yaw_gain = 200      # for scanning rotation
        
        # RC limits
        self.RC_MIN = 1000
        self.RC_MAX = 2000
        self.RC_MID = 1500
        
        # Rate limiting
        self.last_command_time = 0
        self.min_command_interval = 0.1  # 10Hz

    def _clamp(self, val):
        return max(self.RC_MIN, min(self.RC_MAX, int(val)))

    def compute_scan_command(self):
        """Slow yaw rotation to search the room."""
        now = time.time()
        if (now - self.last_command_time) < self.min_command_interval:
            return None
        self.last_command_time = now
        # Gentle yaw right to scan
        return {
            "roll": self.RC_MID,
            "pitch": self.RC_MID,
            "throttle": self.RC_MID,
            "yaw": self._clamp(self.RC_MID + 150),  # gentle right yaw
            "label": "SCANNING"
        }

    def compute_command(self, frame_w, frame_h, face_cx, face_cy, face_w, face_h):
        """
        Returns (rc_command_dict, is_centered)
        
        rc_command_dict has keys: roll, pitch, throttle, yaw, label
        """
        now = time.time()
        if (now - self.last_command_time) < self.min_command_interval:
            return None, False

        fcx = frame_w / 2.0
        fcy = frame_h / 2.0

        # Normalized error: -1.0 (far left/top) to +1.0 (far right/bottom)
        err_x = (face_cx - fcx) / (frame_w / 2.0)  # + = face is right
        err_y = (face_cy - fcy) / (frame_h / 2.0)  # + = face is below

        # Check if centered (within tolerance)
        x_off = abs(face_cx - fcx) / frame_w
        y_off = abs(face_cy - fcy) / frame_h
        centered = (x_off < self.center_tolerance) and (y_off < self.center_tolerance)

        if centered:
            self.last_command_time = now
            return {
                "roll": self.RC_MID,
                "pitch": self.RC_MID,
                "throttle": self.RC_MID,
                "yaw": self.RC_MID,
                "label": "HOVER [LOCKED]"
            }, True

        # Proportional correction
        # Roll: face right of center → roll right (>1500)
        roll = self._clamp(self.RC_MID + err_x * self.roll_gain)
        
        # Throttle: face below center → go down (<1500), above → go up (>1500)
        # Note: err_y positive = face below = need to go DOWN = throttle < 1500
        throttle = self._clamp(self.RC_MID - err_y * self.throttle_gain)
        
        # Build label for console
        parts = []
        if abs(err_x) > 0.1:
            parts.append(f"{'→' if err_x > 0 else '←'} R:{roll}")
        if abs(err_y) > 0.1:
            parts.append(f"{'↓' if err_y > 0 else '↑'} T:{throttle}")
        label = " | ".join(parts) if parts else "ADJUSTING"

        self.last_command_time = now
        return {
            "roll": roll,
            "pitch": self.RC_MID,
            "throttle": throttle,
            "yaw": self.RC_MID,
            "label": label
        }, False
