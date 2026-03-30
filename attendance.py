import json
import csv
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AttendanceManager:
    def __init__(self, database_dir="database", report_file="attendance_report.csv"):
        self.database_dir = database_dir
        self.report_file = report_file
        self.attendance_list = {} # { "Name": {"status": False, "timestamp": None} }
        self.load_students()

    def load_students(self):
        """Loads valid students from the image database names."""
        if not os.path.exists(self.database_dir):
            os.makedirs(self.database_dir)
            
        logger.info("Initializing Attendance Database...")
        # Get names from files in the database directory
        valid_extensions = ('.jpg', '.jpeg', '.png')
        for filename in os.listdir(self.database_dir):
            if filename.lower().endswith(valid_extensions):
                name = os.path.splitext(filename)[0].replace('_', ' ').title()
                if name not in self.attendance_list:
                    self.attendance_list[name] = {"status": False, "timestamp": None}
                    logger.info(f"Student Registered: {name}")

    def mark_present(self, name):
        """Marks a student as present if they are in the database."""
        if name in self.attendance_list:
            if not self.attendance_list[name]["status"]:
                self.attendance_list[name]["status"] = True
                self.attendance_list[name]["timestamp"] = datetime.now().strftime("%H:%M:%S")
                self.save_report()
                return True
        return False

    def is_marked(self, name):
        return self.attendance_list.get(name, {}).get("status", False)

    def get_summary(self):
        present = sum(1 for s in self.attendance_list.values() if s["status"])
        total = len(self.attendance_list)
        return f"PRESENT: {present} / {total}"

    def save_report(self):
        """Exports the current attendance to a CSV file."""
        try:
            with open(self.report_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student Name", "Status", "Time Marked"])
                for name, data in self.attendance_list.items():
                    status = "PRESENT" if data["status"] else "ABSENT"
                    writer.writerow([name, status, data["timestamp"] or "-"])
            # logger.info(f"Attendance Report Updated: {self.report_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    def get_all_records(self):
        return self.attendance_list
