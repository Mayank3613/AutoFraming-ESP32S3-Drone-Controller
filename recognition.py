import os
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    import face_recognition
    FACE_REC_AVAILABLE = True
except ImportError:
    FACE_REC_AVAILABLE = False
    logger.warning("face_recognition library not found. Identification feature disabled.")

class FaceRecognitionProcessor:
    def __init__(self, database_path="database"):
        self.database_path = database_path
        self.known_face_encodings = []
        self.known_face_names = []
        if FACE_REC_AVAILABLE:
            self.load_database()

    def is_available(self):
        return FACE_REC_AVAILABLE

    def load_database(self):
        if not FACE_REC_AVAILABLE:
            return
            
        if not os.path.exists(self.database_path):
            os.makedirs(self.database_path)
            logger.info(f"Created face database directory at {self.database_path}")
            return

        logger.info(f"Loading face database from {self.database_path}...")
        valid_extensions = ('.jpg', '.jpeg', '.png')
        
        for filename in os.listdir(self.database_path):
            if filename.lower().endswith(valid_extensions):
                name = os.path.splitext(filename)[0]
                img_path = os.path.join(self.database_path, filename)
                
                try:
                    image = face_recognition.load_image_file(img_path)
                    # Use num_jitters=0 to avoid dlib API mismatch
                    encodings = face_recognition.face_encodings(image, num_jitters=0)
                    
                    if len(encodings) > 0:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_names.append(name.replace('_', ' ').title())
                        logger.info(f"Loaded and encoded: {name}")
                    else:
                        logger.warning(f"No face found in {filename}, skipping.")
                except Exception as e:
                    logger.error(f"Error processing {filename}: {e}")

        logger.info(f"Finished loading database. Total faces: {len(self.known_face_names)}")

    def identify_face(self, frame):
        """Identifies faces in the given frame. Returns a list of names."""
        if not FACE_REC_AVAILABLE or not self.known_face_encodings:
            return []

        # Convert BGR (OpenCV) to RGB (face_recognition)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Find faces and encodings — use num_jitters=0 to avoid dlib crash
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        
        if not face_locations:
            return []
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=0)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
            name = "Unknown"

            if any(matches):
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]

            face_names.append(name)

        return face_names
    
    def identify_snapshot(self, image_path):
        """Processes a saved snapshot file for face identification."""
        try:
            frame = cv2.imread(image_path)
            if frame is None:
                return []
            return self.identify_face(frame)
        except Exception as e:
            logger.error(f"Snapshot identification error: {e}")
            return []
