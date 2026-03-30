# Drone Controller - No Hardware Test Suite

This is a standalone version of the AutoFraming Drone Controller modified to run without an ESP32, Camera, or Drone. It allows you to verify the AI tracking and control logic using your local webcam.

## 🛠️ Features
- **Local Webcam Support**: Defaults to camera `0` instead of a network stream.
- **Mock Networking**: Simulated connection that always succeeds and logs commands to the console.
- **Full Vision Logic**: Uses the exact same YOLOv8 tracking as the real drone.

## 🚀 How to Run

1. **Install Dependencies** (if you haven't already):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```

3. **In the GUI**:
   - Click **Connect Command**. It will immediately show `SIM STATUS: CONNECTED`.
   - Click **Start Stream**. Your webcam should turn on.
   - Click **ARM**. This simulates enabling the drone's motors.
   - Click **Enable AI Tracking**.
   
4. **Test the Logic**:
   - Step in front of the camera. The AI should draw a box around you.
   - Move left/right/up/down. 
   - Check the **Status Bar** or your **Terminal Console**. You will see logs like `📡 [MOCK SEND] -> LEFT` or `📡 [MOCK SEND] -> RIGHT`. This confirms the software is correctly calculating and "sending" the drone commands.

5. **Manual Override**:
   - Disable AI tracking and use `W/A/S/D` or `Arrow Keys` on your keyboard. The terminal will log these manual commands as well.

## 📁 File Structure
- `main.py`: Modified entry point with simulation logic.
- `network.py`: Simulated command sender.
- `vision.py` / `control.py` / `gui.py`: Core logic files (identical to the original project).
- `yolov8n.pt`: AI model weights.
