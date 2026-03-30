# 🚁 Autonomous Drone Attendance System

> An AI-powered drone system that autonomously flies around a classroom, detects student faces, identifies them against a database, and marks their attendance — all in real-time.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-orange?logo=google)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-purple)
![ESP32](https://img.shields.io/badge/ESP32--CAM-Hardware-red)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Quick Start (No Hardware)](#quick-start-no-hardware)
- [How It Works](#how-it-works)
- [GUI Guide](#gui-guide)
- [Student Database Setup](#student-database-setup)
- [Hardware Setup (ESP32 + Drone)](#hardware-setup-esp32--drone)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

This system replaces manual roll-call attendance with an **autonomous drone** that:

1. **Scans** the classroom by rotating (yaw)
2. **Detects** a student's face using MediaPipe
3. **Centers** on the face using proportional RC control
4. **Captures** a snapshot when perfectly centered
5. **Identifies** the student via face recognition against a local database
6. **Marks** their attendance as ✅ PRESENT
7. **Moves on** to the next student automatically

All computation runs on your **PC/Laptop**. The drone's ESP32-CAM just streams video and relays flight commands.

---

## Architecture

```
┌─────────────────────┐         WiFi AP (192.168.4.1)        ┌──────────────────────────┐
│                     │ ◄──── MJPEG Stream (port 81) ──────  │                          │
│    LAPTOP / PC      │                                      │   ESP32-CAM on Drone     │
│                     │ ────► TCP Commands (port 8080) ───►  │                          │
│  ┌───────────────┐  │        RC:1350,1500,1600,1500        │  ┌────────────────────┐  │
│  │ MediaPipe     │  │                                      │  │ UART (MSP Protocol)│  │
│  │ Face Detection│  │                                      │  └────────┬───────────┘  │
│  └───────┬───────┘  │                                      │           │              │
│          ▼          │                                      │           ▼              │
│  ┌───────────────┐  │                                      │  ┌────────────────────┐  │
│  │ Proportional  │  │                                      │  │ Flight Controller  │  │
│  │ RC Controller │  │                                      │  │ (Betaflight)       │  │
│  └───────┬───────┘  │                                      │  └────────┬───────────┘  │
│          ▼          │                                      │           │              │
│  ┌───────────────┐  │                                      │           ▼              │
│  │ Face          │  │                                      │      ┌─────────┐        │
│  │ Recognition   │  │                                      │      │ MOTORS  │        │
│  └───────┬───────┘  │                                      │      └─────────┘        │
│          ▼          │                                      │                          │
│  ┌───────────────┐  │                                      └──────────────────────────┘
│  │ Attendance    │  │
│  │ Manager + CSV │  │
│  └───────────────┘  │
│                     │
└─────────────────────┘
```

---

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **MediaPipe Face Detection** | Real-time face detection with visual center zone overlay |
| 🕹️ **Proportional RC Control** | Smooth stick values (1000-2000) instead of jerky on/off commands |
| 🧠 **Face Recognition** | Identifies students against a photo database using `face_recognition` + `dlib` |
| 📊 **Live Attendance Table** | GUI shows each student's name, status (✅/❌), and timestamp |
| 📝 **CSV Export** | Automatically generates `attendance_report.csv` after each session |
| 🖥️ **Command Console** | See every AI decision in real-time (scanning, centering, capturing) |
| 📡 **RC Telemetry** | Live display of Roll/Pitch/Throttle/Yaw values being sent to drone |
| 🔄 **State Machine** | Autonomous workflow: SCANNING → CENTERING → PROCESSING → repeat |
| 🧵 **Thread-Safe GUI** | Face recognition runs in background without freezing the interface |
| 🎮 **Manual Override** | Keyboard controls (WASD + Arrows) for manual flight when needed |

---

## Project Structure

```
no-hardware-test/
├── main.py              # Main application controller & state machine
├── gui.py               # PyQt5 GUI with video feed, console, and attendance table
├── vision.py            # MediaPipe face detection with center zone visualization
├── control.py           # Proportional RC controller (1000-2000 stick values)
├── recognition.py       # Face recognition engine (face_recognition + dlib)
├── attendance.py        # Attendance database manager & CSV export
├── network.py           # Network layer (mock for testing, TCP for real drone)
├── requirements.txt     # Python dependencies
├── database/            # Student face photos (one per student)
│   └── Shivam.jpg       # Example: filename = student name
└── captures/            # Auto-generated snapshots (created at runtime)
```

---

## Installation

### Prerequisites

- Python 3.9+
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/Mayank3613/AutoFraming-ESP32S3-Drone-Controller.git
cd AutoFraming-ESP32S3-Drone-Controller
```

### 2. Install Dependencies

```bash
pip install opencv-python mediapipe numpy PyQt5
```

### 3. Install Face Recognition (Optional but recommended)

```bash
# Option A: Using conda (recommended for macOS)
conda install -c conda-forge dlib
pip install face_recognition

# Option B: Using pip (may require cmake)
pip install dlib face_recognition
```

> **Note:** If `dlib` fails to install, the system will still work — face detection and centering will function normally, but face *identification* (matching names) will be disabled.

---

## Quick Start (No Hardware)

You can test the full system using just your **laptop's webcam** — no drone needed.

```bash
python main.py
```

### Step-by-step:

1. **Launch** — The webcam feed starts automatically
2. **Connect** — Click `LINK BRIDGE` (simulates ESP32 connection)
3. **Arm** — Click `ARM` (simulates motor arming)
4. **Start Scanning** — Click `START ATTENDANCE SCAN`
5. **Test** — Position your face in the **yellow center zone** on screen
6. **Observe:**
   - Box turns **green** when you're centered ✅
   - Console shows `🎯 FACE CENTERED → CAPTURING SNAPSHOT`
   - Face recognition runs → `IDENTIFIED: SHIVAM`
   - Attendance table updates with ✅ and timestamp

### What you'll see:

| Element | Location | Purpose |
|---------|----------|---------|
| **Video Feed** | Left panel | Live camera with face detection overlay |
| **Yellow Rectangle** | On video | The "center zone" — face must be inside |
| **Green/Red Box** | Around face | Green = centered, Red = aligning |
| **Command Console** | Below video | Every AI decision logged in real-time |
| **RC Telemetry** | Right panel | Current Roll/Pitch/Throttle/Yaw values |
| **Recognition Box** | Right panel | Shows identified name or "ANALYZING..." |
| **Attendance Table** | Right panel | Live register with ✅/❌ and timestamps |

---

## How It Works

### State Machine

```
         ┌──────────┐
         │   IDLE   │  ← System starts here
         └────┬─────┘
              │ User clicks "START ATTENDANCE SCAN"
              ▼
         ┌──────────┐
    ┌──► │ SCANNING │  ← Drone rotates (YAW) to find faces
    │    └────┬─────┘
    │         │ Face detected!
    │         ▼
    │    ┌──────────┐
    │    │CENTERING │  ← Proportional RC adjustments to center face
    │    └────┬─────┘
    │         │ Face centered (within 15% of frame center)
    │         ▼
    │    ┌──────────┐
    │    │PROCESSING│  ← Snapshot taken, face recognition running
    │    └────┬─────┘
    │         │ Recognition complete, attendance marked
    └─────────┘        ← Returns to SCANNING for next student
```

### Proportional Control

Instead of sending binary `LEFT`/`RIGHT` commands (jerky movement), the controller calculates **proportional RC values**:

```
RC Value = 1500 + (error × gain)
```

| Situation | Roll | Pitch | Throttle | Yaw | Effect |
|-----------|------|-------|----------|-----|--------|
| Face slightly right | 1550 | 1500 | 1500 | 1500 | Gentle right nudge |
| Face far right | 1700 | 1500 | 1500 | 1500 | Strong right correction |
| Face above center | 1500 | 1500 | 1600 | 1500 | Climb slightly |
| Face centered ✅ | 1500 | 1500 | 1500 | 1500 | HOVER — take snapshot |
| No face found | 1500 | 1500 | 1500 | 1650 | Yaw right to scan |

This mimics how a human pilot would fly — **smooth, proportional corrections**.

### Face Recognition Pipeline

```
Snapshot saved → face_recognition detects face locations
              → Encodes face features (128-dimensional vector)
              → Compares against database encodings (Euclidean distance)
              → Match found (distance < 0.6) → Mark as PRESENT
              → No match → Log as "Unknown"
```

---

## GUI Guide

### Keyboard Controls (Manual Mode)

| Key | Command | RC Effect |
|-----|---------|-----------|
| `W` | FORWARD | Pitch 1700 |
| `S` | BACKWARD | Pitch 1300 |
| `A` | LEFT (Roll) | Roll 1300 |
| `D` | RIGHT (Roll) | Roll 1700 |
| `Q` | YAW LEFT | Yaw 1300 |
| `E` | YAW RIGHT | Yaw 1700 |
| `↑` | UP (Altitude) | Throttle 1700 |
| `↓` | DOWN (Altitude) | Throttle 1300 |
| `Space` | HOVER | All 1500 (mid-stick) |

> **Note:** Manual controls are disabled when AI Tracking is active. Toggle off the scan to regain manual control.

---

## Student Database Setup

### Adding Students

1. Navigate to the `database/` folder
2. Add a **clear, front-facing photo** of each student
3. Name the file with the student's name:

```
database/
├── Shivam.jpg
├── John_Doe.jpg        ← Underscores become spaces → "John Doe"
├── Jane_Smith.png      ← Supports .jpg, .jpeg, .png
└── Rahul_Kumar.jpg
```

### Best Practices for Database Photos

- ✅ Front-facing, well-lit photo
- ✅ One face per image
- ✅ Similar angle as the drone camera would see
- ❌ Avoid group photos
- ❌ Avoid heavily filtered images

---

## Hardware Setup (ESP32 + Drone)

### Components Needed

| Component | Purpose |
|-----------|---------|
| ESP32-CAM (AI Thinker) | Camera + WiFi AP |
| Flight Controller (Betaflight-compatible) | Motor control |
| Drone frame + motors + ESCs | Physical flight |
| Battery (3S/4S LiPo) | Power |

### Wiring

```
ESP32-CAM        Flight Controller
─────────        ─────────────────
GND         ───► GND
5V          ───► 5V
TX (GPIO 5) ───► RX (UART2)
RX (GPIO 4) ───► TX (UART2)
```

### ESP32 Firmware

Flash `esp32_bridge/esp32_bridge.ino` using Arduino IDE:

1. Install ESP32 board package in Arduino IDE
2. Select board: **AI Thinker ESP32-CAM**
3. Flash the firmware
4. ESP32 creates WiFi AP: `Drone_ESP32` (password: `password`)

### Connecting to Real Drone

1. Connect your laptop to `Drone_ESP32` WiFi
2. In the app, change IP to `192.168.4.1`
3. Stream URL: `http://192.168.4.1:81/stream`
4. Click **LINK BRIDGE** → **ARM** → **START ATTENDANCE SCAN**

---

## Configuration

Key parameters can be adjusted in `control.py`:

```python
self.center_tolerance = 0.15   # 15% of frame = "centered" (increase for easier lock-on)
self.roll_gain = 300           # How aggressively to correct horizontally
self.throttle_gain = 250       # How aggressively to correct vertically
self.CAPTURE_COOLDOWN = 3.0    # Seconds between snapshots
```

Face recognition tolerance in `recognition.py`:

```python
tolerance=0.6    # Lower = stricter matching, Higher = more lenient
```

---

## Troubleshooting

### `face_recognition` won't install

```bash
# Use conda instead of pip:
conda install -c conda-forge dlib
pip install face_recognition
```

If it still fails, the app will run fine — face detection and centering work normally. Only name identification is disabled.

### GUI freezes when scan starts

This was fixed by moving face recognition to a background thread with Qt signal-based GUI updates. Make sure you're running the latest version.

### Camera not starting

The app defaults to webcam index `0`. If you have multiple cameras, edit `main.py` line:
```python
self.video_thread.set_stream_url("0")  # Change to "1" for external camera
```

### "No face detected" even when looking at camera

- Ensure adequate lighting
- Face the camera directly (MediaPipe works best with front-facing faces)
- Detection confidence is set to `0.5` — lower it in `vision.py` if needed

---

## Tech Stack

| Technology | Usage |
|-----------|-------|
| **Python 3.9+** | Core language |
| **PyQt5** | Desktop GUI framework |
| **OpenCV** | Image processing & camera capture |
| **MediaPipe** | Real-time face detection |
| **face_recognition** | Face identification & matching |
| **dlib** | Face encoding (128-dim vectors) |
| **ESP32-CAM** | On-drone camera & WiFi bridge |
| **Betaflight MSP** | Flight controller communication |

---

## License

This project is for educational and research purposes.

---

<p align="center">
  <b>Built for autonomous classroom attendance 🎓</b>
</p>
