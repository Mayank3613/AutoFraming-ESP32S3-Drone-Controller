import threading
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CommandSender:
    """
    Mock Command Sender for hardware-free testing.
    
    Supports two command formats:
    1. Simple: "LEFT", "RIGHT", "HOVER", "ARM", "DISARM"
    2. Proportional: dict with roll/pitch/throttle/yaw RC values (1000-2000)
    
    In real mode, proportional commands are sent as:
      "RC:roll,pitch,throttle,yaw\n"
    e.g. "RC:1350,1500,1600,1500\n"
    """
    def __init__(self, host: str, port: int = 8080):
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        self.connected = False
        logger.info(f"Initialized MockCommandSender (Target: {self.host}:{self.port})")

    def connect(self):
        with self.lock:
            logger.info(f"Attempting to 'connect' to MOCK ESP32 at {self.host}...")
            self.connected = True
            logger.info(f"SUCCESS: Mock connection established to {self.host}:{self.port}")
            return True

    def disconnect(self):
        with self.lock:
            self.connected = False
            logger.info("Mock disconnection successful.")

    def send_command(self, command):
        """
        Accepts either:
        - str: simple command like "ARM", "HOVER"
        - dict: proportional RC values {roll, pitch, throttle, yaw, label}
        """
        if not self.connected:
            return False
            
        with self.lock:
            if isinstance(command, dict):
                r = command.get("roll", 1500)
                p = command.get("pitch", 1500)
                t = command.get("throttle", 1500)
                y = command.get("yaw", 1500)
                label = command.get("label", "")
                # In real mode this would send: f"RC:{r},{p},{t},{y}\n"
                logger.info(f"📡 [RC] R:{r} P:{p} T:{t} Y:{y} ({label})")
            else:
                clean_cmd = command.strip()
                logger.info(f"📡 [CMD] {clean_cmd}")
            return True
