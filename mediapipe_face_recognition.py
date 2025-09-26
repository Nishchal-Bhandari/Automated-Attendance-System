"""
Enhanced MediaPipe Face Recognition System
Automatic face detection, encoding, and student identification
"""

import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import io
import base64
import hashlib
from typing import List, Dict, Optional, Tuple
import logging

class MediaPipeFaceRecognition:
    """Enhanced MediaPipe-based face recognition system"""
    
    def __init__(self):
        # Initialize MediaPipe
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize face detection and mesh
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # Use full-range model for better detection
            min_detection_confidence=0.7
        )
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Face encoding parameters
        self.encoding_size = 128
        self.similarity_threshold = 0.3  # Lowered from 0.6 to make matching easier
        
        # Logging setup
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces in an image and return their locations and landmarks
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of face detection results with bounding boxes and landmarks
        """
        if image is None:
            print("❌ Face detection: Image is None")
            return []
            
        try:
            print(f"🔎 Face detection: Processing image {image.shape}")
            # Convert BGR to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
                
            # Detect faces
            results = self.face_detection.process(rgb_image)
            
            faces = []
            if results.detections:
                print(f"✅ MediaPipe detected {len(results.detections)} faces")
                h, w = image.shape[:2]
                
                for detection in results.detections:
                    # Get bounding box
                    bbox = detection.location_data.relative_bounding_box
                    
                    # Convert to pixel coordinates
                    x = int(bbox.xmin * w)
                    y = int(bbox.ymin * h)
                    width = int(bbox.width * w)
                    height = int(bbox.height * h)
                    
                    # Ensure coordinates are within image bounds
                    x = max(0, x)
                    y = max(0, y)
                    width = min(width, w - x)
                    height = min(height, h - y)
                    
                    face_info = {
                        'bbox': (x, y, width, height),
                        'confidence': detection.score[0],
                        'landmarks': self._extract_key_landmarks(detection),
                        'face_region': image[y:y+height, x:x+width]
                    }
                    
                    faces.append(face_info)
            else:
                print("❌ MediaPipe: No faces detected in image")
                    
            return faces
            
        except Exception as e:
            self.logger.error(f"Face detection error: {e}")
            return []
    
    def _extract_key_landmarks(self, detection) -> Dict:
        """Extract key facial landmarks from detection"""
        landmarks = {}
        
        if hasattr(detection, 'location_data') and hasattr(detection.location_data, 'relative_keypoints'):
            keypoints = detection.location_data.relative_keypoints
            
            # Map key points (nose tip, left eye, right eye, etc.)
            point_names = ['nose_tip', 'left_eye', 'right_eye', 'mouth_center', 'left_ear', 'right_ear']
            
            for i, point in enumerate(keypoints[:len(point_names)]):
                landmarks[point_names[i]] = (point.x, point.y)
                
        return landmarks
    
    def generate_face_encoding(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate a face encoding/embedding from face image
        
        Args:
            face_image: Cropped face image
            
        Returns:
            Face encoding as numpy array or None if failed
        """
        try:
            if face_image is None or face_image.size == 0:
                return None
                
            # Resize face to standard size
            face_resized = cv2.resize(face_image, (160, 160))
            
            # Convert to RGB
            if len(face_resized.shape) == 3:
                face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
            else:
                face_rgb = face_resized
                
            # Get face mesh landmarks
            results = self.face_mesh.process(face_rgb)
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                
                # Extract landmark coordinates
                landmark_points = []
                for landmark in landmarks.landmark:
                    landmark_points.extend([landmark.x, landmark.y, landmark.z])
                
                # Convert to numpy array and normalize
                encoding = np.array(landmark_points[:self.encoding_size], dtype=np.float32)
                encoding = encoding / np.linalg.norm(encoding)  # Normalize
                
                return encoding
            else:
                # Fallback: use basic image features
                return self._generate_basic_encoding(face_rgb)
                
        except Exception as e:
            self.logger.error(f"Face encoding error: {e}")
            return None
    
    def _generate_basic_encoding(self, face_image: np.ndarray) -> np.ndarray:
        """Generate basic face encoding from image features"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY) if len(face_image.shape) == 3 else face_image
            
            # Resize to standard size
            gray = cv2.resize(gray, (32, 32))
            
            # Flatten and normalize
            encoding = gray.flatten().astype(np.float32)
            encoding = encoding / 255.0  # Normalize to 0-1
            
            # Pad or truncate to desired size
            if len(encoding) > self.encoding_size:
                encoding = encoding[:self.encoding_size]
            elif len(encoding) < self.encoding_size:
                encoding = np.pad(encoding, (0, self.encoding_size - len(encoding)))
                
            return encoding
            
        except Exception as e:
            self.logger.error(f"Basic encoding error: {e}")
            return np.zeros(self.encoding_size)
    
    def compare_faces(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """
        Compare two face encodings and return similarity score
        
        Args:
            encoding1: First face encoding
            encoding2: Second face encoding
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        try:
            if encoding1 is None or encoding2 is None:
                return 0.0
                
            # Ensure same length
            min_len = min(len(encoding1), len(encoding2))
            enc1 = encoding1[:min_len]
            enc2 = encoding2[:min_len]
            
            # Calculate cosine similarity
            dot_product = np.dot(enc1, enc2)
            norm1 = np.linalg.norm(enc1)
            norm2 = np.linalg.norm(enc2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            similarity = dot_product / (norm1 * norm2)
            
            # Convert to 0-1 range
            similarity = (similarity + 1) / 2
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Face comparison error: {e}")
            return 0.0
    
    def identify_faces(self, image: np.ndarray, known_faces: List[Dict]) -> List[Dict]:
        """
        Identify faces in image against known faces database
        
        Args:
            image: Input image
            known_faces: List of known faces with encodings and metadata
            
        Returns:
            List of identified faces with match information
        """
        identified_faces = []
        
        try:
            # Detect faces in image
            detected_faces = self.detect_faces(image)
            
            for face in detected_faces:
                # Generate encoding for detected face
                face_encoding = self.generate_face_encoding(face['face_region'])
                
                if face_encoding is not None:
                    best_match = None
                    best_similarity = 0.0
                    
                    # Compare with known faces
                    for known_face in known_faces:
                        if 'encoding' in known_face:
                            similarity = self.compare_faces(face_encoding, known_face['encoding'])
                            
                            if similarity > best_similarity and similarity > self.similarity_threshold:
                                best_similarity = similarity
                                best_match = known_face
                    
                    # Add identification result
                    face_result = {
                        'bbox': face['bbox'],
                        'confidence': face['confidence'],
                        'similarity': best_similarity,
                        'identified': best_match is not None,
                        'student_info': best_match if best_match else None,
                        'encoding': face_encoding
                    }
                    
                    identified_faces.append(face_result)
                    
        except Exception as e:
            self.logger.error(f"Face identification error: {e}")
            
        return identified_faces
    
    def process_image_for_attendance(self, image_data: bytes) -> Dict:
        """
        Process image for attendance marking - main entry point
        
        Args:
            image_data: Raw image data
            
        Returns:
            Processing results with identified students
        """
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return {'success': False, 'error': 'Invalid image data'}
            
            # Detect faces
            faces = self.detect_faces(image)
            
            result = {
                'success': True,
                'faces_detected': len(faces),
                'faces': []
            }
            
            for face in faces:
                face_info = {
                    'bbox': face['bbox'],
                    'confidence': float(face['confidence']),
                    'encoding': face.get('encoding', None)
                }
                result['faces'].append(face_info)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Image processing error: {e}")
            return {'success': False, 'error': str(e)}
    
    def encode_image_to_base64(self, image: np.ndarray) -> str:
        """Convert image to base64 string"""
        try:
            _, buffer = cv2.imencode('.jpg', image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            return image_base64
        except Exception as e:
            self.logger.error(f"Image encoding error: {e}")
            return ""
    
    def decode_base64_to_image(self, base64_string: str) -> Optional[np.ndarray]:
        """Convert base64 string to image"""
        try:
            image_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return image
        except Exception as e:
            self.logger.error(f"Image decoding error: {e}")
            return None
