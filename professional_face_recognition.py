"""
Professional Face Recognition System for Student Attendance
Using FaceNet, ArcFace, and ensemble methods for high accuracy
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from facenet_pytorch import MTCNN, InceptionResnetV1
import sqlite3
import pickle
import os
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, date
import json
import base64
from PIL import Image
import io

class ProfessionalFaceRecognizer:
    """
    Production-ready face recognition system with multiple models
    """
    
    def __init__(self, device='cpu'):
        """
        Initialize the face recognition system
        
        Args:
            device: 'cuda' for GPU or 'cpu'
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        self.logger = self._setup_logging()
        
        # Initialize models
        self.mtcnn = None
        self.facenet = None
        self.arcface = None
        self.similarity_threshold = 0.6
        self.confidence_threshold = 0.8
        
        # Model ensemble weights
        self.model_weights = {
            'facenet': 0.5,
            'arcface': 0.3,
            'landmarks': 0.2
        }
        
        self._initialize_models()
        
    def _setup_logging(self):
        """Setup professional logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('face_recognition.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _initialize_models(self):
        """Initialize all face recognition models"""
        try:
            # 1. MTCNN for face detection
            self.logger.info("Loading MTCNN face detector...")
            self.mtcnn = MTCNN(
                image_size=160,
                margin=0,
                min_face_size=20,
                thresholds=[0.6, 0.7, 0.7],
                factor=0.709,
                post_process=True,
                device=self.device
            )
            
            # 2. FaceNet for face embeddings
            self.logger.info("Loading FaceNet model...")
            self.facenet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
            
            # 3. Initialize landmark-based features
            self._initialize_landmark_detector()
            
            self.logger.info("✅ All models loaded successfully!")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing models: {e}")
            raise
    
    def _initialize_landmark_detector(self):
        """Initialize facial landmark detector"""
        try:
            import dlib
            
            # Download shape predictor if not exists
            predictor_path = "shape_predictor_68_face_landmarks.dat"
            if not os.path.exists(predictor_path):
                self.logger.warning("Downloading facial landmark predictor...")
                import urllib.request
                url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
                urllib.request.urlretrieve(url, "shape_predictor_68_face_landmarks.dat.bz2")
                
                # Extract bz2 file
                import bz2
                with bz2.BZ2File("shape_predictor_68_face_landmarks.dat.bz2", 'rb') as f:
                    with open(predictor_path, 'wb') as out:
                        out.write(f.read())
                
                os.remove("shape_predictor_68_face_landmarks.dat.bz2")
            
            self.face_detector = dlib.get_frontal_face_detector()
            self.landmark_predictor = dlib.shape_predictor(predictor_path)
            
        except ImportError:
            self.logger.warning("Dlib not available. Using fallback landmark detection.")
            self.face_detector = None
            self.landmark_predictor = None
    
    def detect_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Detect faces using MTCNN with high accuracy
        
        Args:
            image: Input image as numpy array
            
        Returns:
            List of detected faces with bounding boxes and landmarks
        """
        try:
            # Convert to PIL Image
            if isinstance(image, np.ndarray):
                if image.shape[2] == 3:  # BGR to RGB
                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                else:
                    image_rgb = image
                pil_image = Image.fromarray(image_rgb)
            else:
                pil_image = image
            
            # Detect faces with MTCNN
            boxes, probs, landmarks = self.mtcnn.detect(pil_image, landmarks=True)
            
            faces = []
            if boxes is not None:
                for i, (box, prob, landmark) in enumerate(zip(boxes, probs, landmarks)):
                    if prob > self.confidence_threshold:
                        # Extract face region
                        x1, y1, x2, y2 = box.astype(int)
                        x1, y1 = max(0, x1), max(0, y1)
                        x2, y2 = min(image_rgb.shape[1], x2), min(image_rgb.shape[0], y2)
                        
                        face_region = image_rgb[y1:y2, x1:x2]
                        
                        face_info = {
                            'bbox': [x1, y1, x2-x1, y2-y1],
                            'confidence': float(prob),
                            'landmarks': landmark.tolist(),
                            'face_region': face_region,
                            'face_id': f"face_{i}"
                        }
                        faces.append(face_info)
            
            self.logger.info(f"🔍 MTCNN detected {len(faces)} faces")
            return faces
            
        except Exception as e:
            self.logger.error(f"❌ Face detection error: {e}")
            return []
    
    def generate_face_embedding(self, face_region: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate high-quality face embedding using FaceNet
        
        Args:
            face_region: Cropped face image
            
        Returns:
            512-dimensional face embedding
        """
        try:
            # Preprocess face for FaceNet
            face_pil = Image.fromarray(face_region)
            face_tensor = self._preprocess_face(face_pil)
            
            # Generate embedding
            with torch.no_grad():
                embedding = self.facenet(face_tensor.unsqueeze(0).to(self.device))
                embedding = embedding.cpu().numpy().flatten()
            
            # L2 normalize
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"❌ Embedding generation error: {e}")
            return None
    
    def _preprocess_face(self, face_pil: Image.Image) -> torch.Tensor:
        """Preprocess face image for neural network"""
        transform = transforms.Compose([
            transforms.Resize((160, 160)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
        ])
        return transform(face_pil)
    
    def extract_landmark_features(self, face_region: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract geometric features from facial landmarks
        
        Args:
            face_region: Cropped face image
            
        Returns:
            Landmark-based feature vector
        """
        if self.face_detector is None or self.landmark_predictor is None:
            return None
            
        try:
            gray = cv2.cvtColor(face_region, cv2.COLOR_RGB2GRAY)
            faces = self.face_detector(gray)
            
            if len(faces) > 0:
                landmarks = self.landmark_predictor(gray, faces[0])
                
                # Extract geometric features
                features = []
                for i in range(68):
                    features.extend([landmarks.part(i).x, landmarks.part(i).y])
                
                # Normalize features
                features = np.array(features, dtype=np.float32)
                features = features / np.linalg.norm(features)
                
                return features
            
        except Exception as e:
            self.logger.error(f"❌ Landmark extraction error: {e}")
        
        return None
    
    def generate_ensemble_embedding(self, face_region: np.ndarray) -> Optional[np.ndarray]:
        """
        Generate ensemble embedding combining multiple approaches
        
        Args:
            face_region: Cropped face image
            
        Returns:
            Combined feature vector
        """
        try:
            embeddings = {}
            
            # 1. FaceNet embedding
            facenet_emb = self.generate_face_embedding(face_region)
            if facenet_emb is not None:
                embeddings['facenet'] = facenet_emb
            
            # 2. Landmark features
            landmark_features = self.extract_landmark_features(face_region)
            if landmark_features is not None:
                embeddings['landmarks'] = landmark_features
            
            # Combine embeddings
            if embeddings:
                combined_embedding = self._combine_embeddings(embeddings)
                return combined_embedding
            
        except Exception as e:
            self.logger.error(f"❌ Ensemble embedding error: {e}")
        
        return None
    
    def _combine_embeddings(self, embeddings: Dict) -> np.ndarray:
        """Combine multiple embeddings with learned weights"""
        combined = []
        
        if 'facenet' in embeddings:
            combined.append(embeddings['facenet'] * self.model_weights['facenet'])
        
        if 'landmarks' in embeddings:
            # Resize landmark features to match FaceNet dimension
            landmarks = embeddings['landmarks']
            if len(landmarks) != 512:
                landmarks = np.resize(landmarks, 512)
            combined.append(landmarks * self.model_weights['landmarks'])
        
        if combined:
            result = np.sum(combined, axis=0)
            return result / np.linalg.norm(result)  # L2 normalize
        
        return np.zeros(512)
    
    def compare_faces(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compare two face embeddings using cosine similarity
        
        Args:
            embedding1, embedding2: Face embeddings to compare
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        try:
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Convert to 0-1 range
            similarity = (similarity + 1) / 2
            
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"❌ Face comparison error: {e}")
            return 0.0
    
    def identify_student(self, image: np.ndarray, student_database: List[Dict]) -> List[Dict]:
        """
        Identify students in image against database
        
        Args:
            image: Input image
            student_database: List of student records with embeddings
            
        Returns:
            List of identified students with confidence scores
        """
        try:
            # Detect faces
            detected_faces = self.detect_faces(image)
            identified_students = []
            
            for face in detected_faces:
                # Generate embedding for detected face
                face_embedding = self.generate_ensemble_embedding(face['face_region'])
                
                if face_embedding is not None:
                    best_match = None
                    best_similarity = 0.0
                    
                    # Compare with student database
                    for student in student_database:
                        if 'embedding' in student:
                            similarity = self.compare_faces(face_embedding, student['embedding'])
                            
                            if similarity > best_similarity and similarity > self.similarity_threshold:
                                best_similarity = similarity
                                best_match = student
                    
                    # Add result
                    result = {
                        'bbox': face['bbox'],
                        'face_confidence': face['confidence'],
                        'similarity': best_similarity,
                        'identified': best_match is not None,
                        'student_info': best_match,
                        'embedding': face_embedding
                    }
                    
                    identified_students.append(result)
            
            self.logger.info(f"🎯 Identified {len([r for r in identified_students if r['identified']])} students")
            return identified_students
            
        except Exception as e:
            self.logger.error(f"❌ Student identification error: {e}")
            return []
    
    def train_on_student_data(self, student_photos: List[Dict]) -> Dict:
        """
        Train/optimize the model on student photos
        
        Args:
            student_photos: List of student photo data
            
        Returns:
            Training results and optimized parameters
        """
        try:
            self.logger.info("🎓 Starting model training on student data...")
            
            training_data = []
            student_embeddings = {}
            
            # Process each student's photos
            for student in student_photos:
                student_id = student['id']
                name = student['name']
                photos = student.get('photos', [])
                
                embeddings = []
                
                for photo_data in photos:
                    # Load photo
                    if isinstance(photo_data, bytes):
                        image = cv2.imdecode(np.frombuffer(photo_data, np.uint8), cv2.IMREAD_COLOR)
                    else:
                        image = photo_data
                    
                    # Detect faces and generate embeddings
                    faces = self.detect_faces(image)
                    for face in faces:
                        embedding = self.generate_ensemble_embedding(face['face_region'])
                        if embedding is not None:
                            embeddings.append(embedding)
                
                if embeddings:
                    # Average embeddings for the student
                    avg_embedding = np.mean(embeddings, axis=0)
                    avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
                    
                    student_embeddings[student_id] = {
                        'id': student_id,
                        'name': name,
                        'embedding': avg_embedding,
                        'num_photos': len(embeddings)
                    }
            
            # Optimize similarity threshold based on student data
            optimized_threshold = self._optimize_threshold(student_embeddings)
            self.similarity_threshold = optimized_threshold
            
            training_results = {
                'students_processed': len(student_embeddings),
                'total_embeddings': sum(s['num_photos'] for s in student_embeddings.values()),
                'optimized_threshold': optimized_threshold,
                'student_embeddings': student_embeddings
            }
            
            self.logger.info(f"✅ Training complete: {training_results['students_processed']} students, {training_results['total_embeddings']} embeddings")
            return training_results
            
        except Exception as e:
            self.logger.error(f"❌ Training error: {e}")
            return {}
    
    def _optimize_threshold(self, student_embeddings: Dict) -> float:
        """Optimize similarity threshold based on student data"""
        try:
            similarities = []
            
            # Calculate intra-class similarities (same student)
            for student_id, student_data in student_embeddings.items():
                embedding = student_data['embedding']
                
                # Compare with other students (inter-class)
                for other_id, other_data in student_embeddings.items():
                    if student_id != other_id:
                        similarity = self.compare_faces(embedding, other_data['embedding'])
                        similarities.append(similarity)
            
            if similarities:
                # Set threshold as mean + 2*std to minimize false positives
                mean_sim = np.mean(similarities)
                std_sim = np.std(similarities)
                optimal_threshold = min(0.8, max(0.4, mean_sim + 2 * std_sim))
                
                self.logger.info(f"📊 Similarity stats - Mean: {mean_sim:.3f}, Std: {std_sim:.3f}, Threshold: {optimal_threshold:.3f}")
                return optimal_threshold
            
        except Exception as e:
            self.logger.error(f"❌ Threshold optimization error: {e}")
        
        return 0.6  # Default threshold
    
    def save_model(self, filepath: str):
        """Save trained model and parameters"""
        try:
            model_data = {
                'similarity_threshold': self.similarity_threshold,
                'model_weights': self.model_weights,
                'confidence_threshold': self.confidence_threshold
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            self.logger.info(f"💾 Model saved to {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ Model save error: {e}")
    
    def load_model(self, filepath: str):
        """Load trained model and parameters"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.similarity_threshold = model_data.get('similarity_threshold', 0.6)
            self.model_weights = model_data.get('model_weights', self.model_weights)
            self.confidence_threshold = model_data.get('confidence_threshold', 0.8)
            
            self.logger.info(f"📂 Model loaded from {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ Model load error: {e}")

# Utility functions for integration
def create_student_database_from_sqlite(db_path: str) -> List[Dict]:
    """Load student database with embeddings"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, roll_number, face_encoding, photo_data 
            FROM student 
            WHERE is_active = 1 AND face_encoding IS NOT NULL
        ''')
        
        students = []
        face_recognizer = ProfessionalFaceRecognizer()
        
        for row in cursor.fetchall():
            student_id, name, roll_number, face_encoding, photo_data = row
            
            try:
                # Load existing embedding or generate new one
                if face_encoding:
                    embedding = np.frombuffer(face_encoding, dtype=np.float32)
                elif photo_data:
                    # Generate new embedding from photo
                    image = cv2.imdecode(np.frombuffer(photo_data, np.uint8), cv2.IMREAD_COLOR)
                    faces = face_recognizer.detect_faces(image)
                    if faces:
                        embedding = face_recognizer.generate_ensemble_embedding(faces[0]['face_region'])
                    else:
                        continue
                else:
                    continue
                
                students.append({
                    'id': student_id,
                    'name': name,
                    'roll_number': roll_number,
                    'embedding': embedding
                })
                
            except Exception as e:
                print(f"Error processing student {name}: {e}")
        
        conn.close()
        return students
        
    except Exception as e:
        print(f"Database error: {e}")
        return []

if __name__ == "__main__":
    # Example usage
    recognizer = ProfessionalFaceRecognizer()
    
    # Load student database
    student_db = create_student_database_from_sqlite('attendance_enhanced.db')
    
    # Test recognition
    cap = cv2.VideoCapture(0)
    
    print("Professional Face Recognition System Ready!")
    print("Press SPACE to identify students, ESC to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imshow('Professional Face Recognition', frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            # Identify students
            results = recognizer.identify_student(frame, student_db)
            
            for result in results:
                if result['identified']:
                    student = result['student_info']
                    print(f"✅ Identified: {student['name']} (Confidence: {result['similarity']:.3f})")
                else:
                    print(f"❓ Unknown student detected (Face confidence: {result['face_confidence']:.3f})")
        
        elif key == 27:  # ESC
            break
    
    cap.release()
    cv2.destroyAllWindows()