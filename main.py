import sys
import cv2
import time
import os
import datetime
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QObject
from PyQt5.QtGui import QImage, QPixmap
import numpy as np

from gui import DroneGUI
from network import CommandSender 
from vision import VisionProcessor
from control import VisualServoController
from recognition import FaceRecognitionProcessor
from attendance import AttendanceManager


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    log_signal = pyqtSignal(str)
    tracking_data_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.stream_url = 0  
        self.vision = VisionProcessor()
        
    def set_stream_url(self, url):
        if isinstance(url, str) and url.isdigit():
            self.stream_url = int(url)
        else:
            self.stream_url = url
        
    def run(self):
        cap = cv2.VideoCapture(self.stream_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        fps_start = time.time()
        fps_count = 0

        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                fps_count += 1
                elapsed = time.time() - fps_start
                if elapsed > 1.0:
                    self.log_signal.emit(f"FPS: {fps_count / elapsed:.1f}")
                    fps_start = time.time()
                    fps_count = 0

                processed, target = self.vision.process_frame(frame)
                
                if target:
                    h, w, _ = processed.shape
                    self.tracking_data_signal.emit((target, w, h))
                else:
                    self.tracking_data_signal.emit(None)

                self.change_pixmap_signal.emit(processed)
            else:
                time.sleep(0.5)
                
        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()


class AppController(QObject):
    recognition_done_signal = pyqtSignal(str)
    _log_signal = pyqtSignal(str)
    _state_signal = pyqtSignal(str)
    _refresh_table_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.gui = DroneGUI()
        
        self.cmd_sender = CommandSender("localhost", 8080)
        self.servo = VisualServoController()
        self.recognition = FaceRecognitionProcessor()
        self.attendance = AttendanceManager()
        
        self.video_thread = VideoThread()
        self.ai_tracking_enabled = False
        self.last_rc_command = None
        
        # State
        self.state = "IDLE"
        self.last_capture_time = 0
        self.CAPTURE_COOLDOWN = 3.0
        
        self.capture_dir = "captures"
        os.makedirs(self.capture_dir, exist_ok=True)

        # ---- Wire signals ----
        self.gui.connect_signal.connect(self.connect_sim)
        self.gui.disconnect_signal.connect(self.disconnect_sim)
        self.gui.start_stream_signal.connect(self.start_stream)
        self.gui.stop_stream_signal.connect(self.stop_stream)
        self.gui.tracking_toggle_signal.connect(self.toggle_tracking)
        self.gui.manual_command_signal.connect(self.send_manual_command)
        self.gui.arm_signal.connect(self.arm_sim)
        self.gui.disarm_signal.connect(self.disarm_sim)

        self.video_thread.change_pixmap_signal.connect(self.gui.update_frame)
        self.video_thread.log_signal.connect(self._on_fps)
        self.video_thread.tracking_data_signal.connect(self.handle_tracking)
        self.recognition_done_signal.connect(self.gui.update_recognition)
        
        # Thread-safe signals
        self._log_signal.connect(self.gui.add_log)
        self._state_signal.connect(self._apply_state)
        self._refresh_table_signal.connect(self._refresh_attendance)
        
        # Initialize UI
        self._refresh_attendance()
        self.gui.add_log("System initialized. Camera starting...")
        
        # Auto-start local camera for no-hardware mode
        self.video_thread.set_stream_url("0")
        self.video_thread.start()
        
        self.gui.show()

    # ---- Thread-safe helpers (callable from any thread) ----
    def safe_log(self, msg):
        self._log_signal.emit(msg)
    
    @pyqtSlot(str)
    def _apply_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.gui.state_label.setText(f"STATE: {new_state}")
            self.gui.add_log(f"STATE → {new_state}")

    def set_state(self, new_state):
        self._state_signal.emit(new_state)
    
    @pyqtSlot()
    def _refresh_attendance(self):
        records = self.attendance.get_all_records()
        self.gui.summary_label.setText(self.attendance.get_summary())
        self.gui.update_attendance_table(records)

    # ---- Sim controls ----
    @pyqtSlot(str, int)
    def connect_sim(self, ip, port):
        self.cmd_sender.host = ip
        self.cmd_sender.port = port
        self.cmd_sender.connect()
        self.gui.update_status("CONNECTED")
        self.gui.add_log(f"Bridge linked to {ip}:{port}")

    @pyqtSlot()
    def disconnect_sim(self):
        self.cmd_sender.disconnect()
        self.gui.update_status("DISCONNECTED")

    @pyqtSlot(str)
    def start_stream(self, url):
        self.video_thread._run_flag = True
        self.video_thread.start()

    @pyqtSlot()
    def stop_stream(self):
        self.video_thread.stop()

    @pyqtSlot(bool)
    def toggle_tracking(self, checked):
        self.ai_tracking_enabled = checked
        self.video_thread.vision.enable_tracking(checked)
        if checked:
            self.state = "SCANNING"
            self.gui.state_label.setText("STATE: SCANNING")
            self.gui.add_log(">>> ATTENDANCE SCAN STARTED")
        else:
            self.state = "IDLE"
            self.gui.state_label.setText("STATE: IDLE")
            self.cmd_sender.send_command("HOVER")
            self.gui.update_recognition("WAITING...")
            self.gui.add_log(">>> SCAN STOPPED")

    # ---- Capture & Recognition ----
    def force_capture(self):
        pixmap = self.gui.video_label.pixmap()
        if pixmap:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.capture_dir, f"snap_{ts}.jpg")
            pixmap.toImage().save(path)
            self.gui.add_log(f"📸 Snapshot → {path}")
            
            if self.recognition.is_available():
                threading.Thread(target=self._run_recognition, args=(path,), daemon=True).start()
            else:
                self.recognition_done_signal.emit("RECOGNITION UNAVAILABLE")
                self.set_state("SCANNING")

    def _run_recognition(self, image_path):
        """Background thread. All GUI updates via signals."""
        self.recognition_done_signal.emit("ANALYZING...")
        
        names = self.recognition.identify_snapshot(image_path)
        
        if not names:
            self.recognition_done_signal.emit("NO FACE DETECTED")
            self.safe_log("Recognition: No face found in snapshot.")
        else:
            display = ", ".join(names).upper()
            self.recognition_done_signal.emit(f"IDENTIFIED: {display}")
            
            for name in names:
                if name == "Unknown":
                    self.safe_log("⚠️ Unknown person detected.")
                elif self.attendance.mark_present(name):
                    self.safe_log(f"✅ {name} marked PRESENT!")
                else:
                    self.safe_log(f"ℹ️ {name} already marked.")
            
            # Refresh table on main thread
            self._refresh_table_signal.emit()
        
        time.sleep(1.5)
        if self.ai_tracking_enabled:
            self.set_state("SCANNING")

    # ---- Manual controls ----
    @pyqtSlot(str)
    def send_manual_command(self, cmd):
        if not self.ai_tracking_enabled:
            self.cmd_sender.send_command(cmd)
            self.gui.cmd_label.setText(f"CMD: {cmd}")

    @pyqtSlot()
    def arm_sim(self):
        self.cmd_sender.send_command("ARM")
        self.gui.update_status("ARMED")
        self.gui.add_log("Motors ARMED")

    @pyqtSlot()
    def disarm_sim(self):
        self.cmd_sender.send_command("DISARM")
        self.gui.update_status("DISARMED")
        self.gui.add_log("Motors DISARMED")

    # ---- FPS display ----
    @pyqtSlot(str)
    def _on_fps(self, fps_str):
        self.gui.fps_label.setText(fps_str)
        self.gui.state_label.setText(f"STATE: {self.state}")

    # ---- Send RC command to drone ----
    def send_rc(self, rc_cmd):
        """Send a proportional RC command dict to the drone."""
        if rc_cmd is None:
            return
        self.cmd_sender.send_command(rc_cmd)
        label = rc_cmd.get("label", "")
        r, p, t, y = rc_cmd["roll"], rc_cmd["pitch"], rc_cmd["throttle"], rc_cmd["yaw"]
        self.gui.rc_label.setText(f"RC: {r}/{p}/{t}/{y}")
        self.gui.cmd_label.setText(f"CMD: {label}")
        self.last_rc_command = rc_cmd

    # ---- Core tracking loop ----
    @pyqtSlot(object)
    def handle_tracking(self, data):
        if not self.ai_tracking_enabled or self.state == "PROCESSING":
            return
            
        if data is None:
            # No face — scan the room
            if self.state != "SCANNING":
                self.state = "SCANNING"
                self.gui.state_label.setText("STATE: SCANNING")
            rc = self.servo.compute_scan_command()
            self.send_rc(rc)
            return
            
        # Face found!
        if self.state == "SCANNING":
            self.state = "CENTERING"
            self.gui.state_label.setText("STATE: CENTERING")
            self.gui.add_log("👤 Face detected — centering...")

        target, w, h = data
        x1, y1, x2, y2, cx, cy, face_w, face_h, area, conf = target
        
        rc_cmd, centered = self.servo.compute_command(w, h, cx, cy, face_w, face_h)
        
        if rc_cmd:
            self.send_rc(rc_cmd)
            
        # Face centered = take the shot
        if centered:
            now = time.time()
            if now - self.last_capture_time > self.CAPTURE_COOLDOWN:
                self.gui.add_log("🎯 FACE CENTERED → CAPTURING SNAPSHOT")
                self.state = "PROCESSING"
                self.gui.state_label.setText("STATE: PROCESSING")
                self.force_capture()
                self.last_capture_time = now

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    controller = AppController()
    controller.run()
