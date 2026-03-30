import sys
import numpy as np
import cv2
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QGroupBox, QGridLayout, QFrame, QPlainTextEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor, QTextCursor
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

class PremiumButton(QPushButton):
    def __init__(self, text, color="#3498db"):
        super().__init__(text)
        self.base_color = color
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {color}cc; }}
            QPushButton:pressed {{ background-color: {color}99; }}
            QPushButton:disabled {{ background-color: #333; color: #666; }}
        """)

class DroneGUI(QWidget):
    connect_signal = pyqtSignal(str, int)
    disconnect_signal = pyqtSignal()
    start_stream_signal = pyqtSignal(str)
    stop_stream_signal = pyqtSignal()
    tracking_toggle_signal = pyqtSignal(bool)
    capture_signal = pyqtSignal()
    manual_command_signal = pyqtSignal(str)
    arm_signal = pyqtSignal()
    disarm_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('AERO-ATTENDANCE COMMAND CENTER')
        self.resize(1400, 920)
        self.setStyleSheet("""
            background-color: #0F0F0F; 
            color: #E0E0E0; 
            font-family: 'Helvetica Neue', 'Arial', sans-serif;
        """)
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # ==================== LEFT PANEL ====================
        left_panel = QVBoxLayout()
        left_panel.setSpacing(8)
        
        # Header
        header = QHBoxLayout()
        self.title_label = QLabel("DRONE ATTENDANCE SYSTEM")
        self.title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #3498db; letter-spacing: 2px;")
        header.addWidget(self.title_label)
        header.addStretch()
        self.status_label = QLabel("SYSTEM IDLE")
        self.status_label.setStyleSheet("background-color: #1A1A1A; padding: 4px 12px; border-radius: 10px; font-weight: bold; color: #f1c40f; border: 1px solid #333; font-size: 11px;")
        header.addWidget(self.status_label)
        left_panel.addLayout(header)
        
        # Video Container
        video_container = QFrame()
        video_container.setStyleSheet("background-color: #000; border-radius: 10px; border: 1px solid #222;")
        video_vbox = QVBoxLayout(video_container)
        video_vbox.setContentsMargins(4, 4, 4, 4)
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(780, 480)
        video_vbox.addWidget(self.video_label)
        left_panel.addWidget(video_container)
        
        # Command Console
        console_box = self._group("COMMAND CONSOLE")
        console_box.setFixedHeight(180)
        self.console_log = QPlainTextEdit()
        self.console_log.setReadOnly(True)
        self.console_log.setMaximumBlockCount(200)  # limit memory
        self.console_log.setStyleSheet("""
            background-color: #000; 
            color: #2ecc71; 
            font-family: 'Courier New', monospace; 
            font-size: 11px; 
            border: none;
            padding: 5px;
        """)
        console_box.layout().addWidget(self.console_log)
        left_panel.addWidget(console_box)
        
        main_layout.addLayout(left_panel, stretch=3)
        
        # ==================== RIGHT PANEL ====================
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)
        
        # Telemetry
        tele_box = self._group("TELEMETRY")
        tele_grid = QGridLayout()
        self.fps_label = QLabel("FPS: --")
        self.cmd_label = QLabel("CMD: IDLE")
        self.state_label = QLabel("STATE: IDLE")
        self.rc_label = QLabel("RC: 1500/1500/1500/1500")
        for i, lbl in enumerate([self.fps_label, self.cmd_label, self.state_label, self.rc_label]):
            lbl.setStyleSheet("font-size: 10px; color: #888; font-weight: bold;")
            tele_grid.addWidget(lbl, i // 2, i % 2)
        tele_box.layout().addLayout(tele_grid)
        right_panel.addWidget(tele_box)
        
        # AI Control
        ai_box = self._group("AI ATTENDANCE")
        ai_layout = QVBoxLayout()
        self.btn_tracking = PremiumButton("START ATTENDANCE SCAN", "#9b59b6")
        self.btn_tracking.setCheckable(True)
        self.btn_tracking.toggled.connect(self._on_tracking_toggled)
        ai_layout.addWidget(self.btn_tracking)
        self.rec_result = QLabel("WAITING...")
        self.rec_result.setStyleSheet("background-color: #000; border: 1px solid #9b59b6; border-radius: 6px; padding: 8px; color: #9b59b6; font-weight: bold; font-family: monospace; font-size: 12px;")
        self.rec_result.setAlignment(Qt.AlignCenter)
        self.rec_result.setWordWrap(True)
        ai_layout.addWidget(self.rec_result)
        ai_box.layout().addLayout(ai_layout)
        right_panel.addWidget(ai_box)

        # Summary
        self.summary_label = QLabel("PRESENT: 0 / 0")
        self.summary_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 13px; background: #1A1A1A; border: 1px solid #2ecc71; padding: 8px; border-radius: 6px;")
        self.summary_label.setAlignment(Qt.AlignCenter)
        right_panel.addWidget(self.summary_label)
        
        # ---- ATTENDANCE TABLE ----
        att_box = self._group("ATTENDANCE REGISTER")
        self.att_table = QTableWidget()
        self.att_table.setColumnCount(4)
        self.att_table.setHorizontalHeaderLabels(["#", "Student", "Status", "Time"])
        self.att_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.att_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.att_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.att_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.att_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.att_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.att_table.verticalHeader().setVisible(False)
        self.att_table.setStyleSheet("""
            QTableWidget {
                background-color: #0A0A0A;
                color: #ccc;
                border: none;
                font-size: 11px;
                gridline-color: #222;
            }
            QHeaderView::section {
                background-color: #1A1A1A;
                color: #888;
                border: 1px solid #222;
                padding: 4px;
                font-weight: bold;
                font-size: 10px;
            }
        """)
        att_box.layout().addWidget(self.att_table)
        right_panel.addWidget(att_box)

        # Connection
        conn_box = self._group("BRIDGE")
        conn_grid = QGridLayout()
        self.ip_input = QLineEdit("127.0.0.1")
        self.ip_input.setStyleSheet("background-color: #1E1E1E; border: 1px solid #333; border-radius: 4px; padding: 5px; color: #fff; font-size: 11px;")
        conn_grid.addWidget(self.ip_input, 0, 0, 1, 2)
        self.btn_connect = PremiumButton("LINK BRIDGE", "#2ecc71")
        self.btn_connect.clicked.connect(self._on_connect)
        conn_grid.addWidget(self.btn_connect, 1, 0)
        self.btn_arm = PremiumButton("ARM", "#e74c3c")
        self.btn_arm.clicked.connect(lambda: self.arm_signal.emit())
        conn_grid.addWidget(self.btn_arm, 1, 1)
        conn_box.layout().addLayout(conn_grid)
        right_panel.addWidget(conn_box)
        
        main_layout.addLayout(right_panel, stretch=1)
        self.setLayout(main_layout)

    # ---------- Helpers ----------
    def _group(self, title):
        g = QGroupBox(title)
        g.setStyleSheet("""
            QGroupBox {
                border: 1px solid #222;
                border-radius: 8px;
                margin-top: 12px;
                background-color: #111;
                color: #555;
                font-weight: bold;
                font-size: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 18, 8, 8)
        g.setLayout(layout)
        return g

    def _on_connect(self):
        ip = self.ip_input.text()
        self.connect_signal.emit(ip, 8080)
        self.btn_connect.setEnabled(False)
        self.btn_connect.setText("LINKED")

    def _on_tracking_toggled(self, checked):
        if checked:
            self.btn_tracking.setText("STOP SCAN")
        else:
            self.btn_tracking.setText("START ATTENDANCE SCAN")
        self.tracking_toggle_signal.emit(checked)

    # ---------- Public Slots ----------
    @pyqtSlot(np.ndarray)
    def update_frame(self, cv_img):
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qt_img).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pix)

    @pyqtSlot(str)
    def add_log(self, text):
        self.console_log.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")
        self.console_log.moveCursor(QTextCursor.End)

    @pyqtSlot(str)
    def update_status(self, text):
        self.status_label.setText(text)

    @pyqtSlot(str)
    def update_recognition(self, result_text):
        self.rec_result.setText(result_text)
        if "UNKNOWN" in result_text or "NO FACE" in result_text or "UNAVAILABLE" in result_text or "ERROR" in result_text:
            self.rec_result.setStyleSheet(self.rec_result.styleSheet().replace("#9b59b6", "#e74c3c").replace("#2ecc71", "#e74c3c"))
        elif "IDENTIFIED" in result_text:
            self.rec_result.setStyleSheet(self.rec_result.styleSheet().replace("#9b59b6", "#2ecc71").replace("#e74c3c", "#2ecc71"))

    def update_attendance_table(self, records):
        """
        records: dict of { "Name": {"status": bool, "timestamp": str|None} }
        """
        self.att_table.setRowCount(len(records))
        for i, (name, data) in enumerate(records.items()):
            # #
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.att_table.setItem(i, 0, num_item)
            
            # Name
            self.att_table.setItem(i, 1, QTableWidgetItem(name))
            
            # Status
            if data["status"]:
                status_item = QTableWidgetItem("✅ PRESENT")
                status_item.setForeground(QColor("#2ecc71"))
            else:
                status_item = QTableWidgetItem("❌ ABSENT")
                status_item.setForeground(QColor("#e74c3c"))
            status_item.setTextAlignment(Qt.AlignCenter)
            self.att_table.setItem(i, 2, status_item)
            
            # Time
            time_str = data["timestamp"] or "—"
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignCenter)
            self.att_table.setItem(i, 3, time_item)

    def keyPressEvent(self, event):
        key = event.key()
        mapping = {
            Qt.Key_W: "FORWARD", Qt.Key_S: "BACKWARD",
            Qt.Key_A: "LEFT", Qt.Key_D: "RIGHT",
            Qt.Key_Q: "YAW_LEFT", Qt.Key_E: "YAW_RIGHT",
            Qt.Key_Up: "UP", Qt.Key_Down: "DOWN",
            Qt.Key_Space: "HOVER"
        }
        cmd = mapping.get(key, "")
        if cmd:
            self.manual_command_signal.emit(cmd)
