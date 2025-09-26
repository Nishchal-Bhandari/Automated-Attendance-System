"""
Integration script for Professional Face Recognition System
Integrates with existing Flask attendance application
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from professional_face_recognition import ProfessionalFaceRecognizer, create_student_database_from_sqlite
import cv2
import numpy as np
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, date
import base64
import io
from PIL import Image

class ProfessionalAttendanceSystem:
    """
    Professional attendance system integration
    """
    
    def __init__(self, db_path='attendance_enhanced.db', model_path='trained_face_model.pkl'):
        self.db_path = db_path
        self.model_path = model_path
        self.face_recognizer = ProfessionalFaceRecognizer()
        self.student_database = []
        
        # Load trained model if available
        if os.path.exists(model_path):
            self.face_recognizer.load_model(model_path)
            print("✅ Loaded trained face recognition model")
        else:
            print("⚠️ No trained model found. Using default parameters.")
        
        # Load student database
        self.reload_student_database()
    
    def reload_student_database(self):
        """Reload student database from SQLite"""
        try:
            self.student_database = create_student_database_from_sqlite(self.db_path)
            print(f"📊 Loaded {len(self.student_database)} students from database")
        except Exception as e:
            print(f"❌ Error loading student database: {e}")
            self.student_database = []
    
    def process_attendance_image(self, image_data, method='camera'):
        """
        Process image for attendance marking
        
        Args:
            image_data: Image data (bytes, base64, or numpy array)
            method: Attendance marking method
            
        Returns:
            Dictionary with results
        """
        try:
            # Convert image data to numpy array
            image = self._process_image_data(image_data)
            if image is None:
                return {'success': False, 'error': 'Invalid image data'}
            
            # Identify students
            results = self.face_recognizer.identify_student(image, self.student_database)
            
            # Mark attendance for identified students
            attendance_results = []
            for result in results:
                if result['identified']:
                    student_info = result['student_info']
                    
                    # Mark attendance in database
                    attendance_success = self._mark_attendance(
                        student_info['id'],
                        result['similarity'],
                        method
                    )
                    
                    attendance_results.append({
                        'student_id': student_info['id'],
                        'student_name': student_info['name'],
                        'roll_number': student_info['roll_number'],
                        'similarity': result['similarity'],
                        'bbox': result['bbox'],
                        'attendance_marked': attendance_success
                    })
            
            return {
                'success': True,
                'total_faces': len(results),
                'identified_students': len(attendance_results),
                'results': attendance_results,
                'all_faces': results  # Include all detected faces
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _process_image_data(self, image_data):
        """Convert various image data formats to numpy array"""
        try:
            if isinstance(image_data, str):
                # Base64 encoded image
                if 'data:image' in image_data:
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                image_array = np.frombuffer(image_bytes, np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
            elif isinstance(image_data, bytes):
                # Raw bytes
                image_array = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
            elif isinstance(image_data, np.ndarray):
                # Already numpy array
                image = image_data
                
            else:
                return None
            
            return image
            
        except Exception as e:
            print(f"❌ Image processing error: {e}")
            return None
    
    def _mark_attendance(self, student_id, confidence, method):
        """Mark attendance in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if already marked today
            today = date.today()
            cursor.execute('''
                SELECT id FROM attendance 
                WHERE student_id = ? AND date = ?
            ''', (student_id, today))
            
            if cursor.fetchone():
                conn.close()
                return False  # Already marked
            
            # Mark new attendance
            cursor.execute('''
                INSERT INTO attendance (student_id, date, time_in, method, confidence_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, today, datetime.now().time(), method, confidence, datetime.now()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Attendance marking error: {e}")
            return False
    
    def add_student_with_photo(self, student_data, photo_data):
        """
        Add new student with professional face encoding
        
        Args:
            student_data: Dictionary with student information
            photo_data: Photo data (bytes)
            
        Returns:
            Success status and results
        """
        try:
            # Process photo and generate embedding
            image = cv2.imdecode(np.frombuffer(photo_data, np.uint8), cv2.IMREAD_COLOR)
            faces = self.face_recognizer.detect_faces(image)
            
            if not faces:
                return {'success': False, 'error': 'No face detected in photo'}
            
            # Generate high-quality embedding
            embedding = self.face_recognizer.generate_ensemble_embedding(faces[0]['face_region'])
            
            if embedding is None:
                return {'success': False, 'error': 'Failed to generate face embedding'}
            
            # Save to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO student (
                    name, roll_number, class_name, section, parent_name,
                    phone_number, parent_phone, address, photo_data, 
                    face_encoding, face_confidence, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                student_data.get('name'),
                student_data.get('roll_number'),
                student_data.get('class_name', ''),
                student_data.get('section', ''),
                student_data.get('parent_name', ''),
                student_data.get('phone_number', ''),
                student_data.get('parent_phone', ''),
                student_data.get('address', ''),
                photo_data,
                embedding.astype(np.float32).tobytes(),
                faces[0]['confidence'],
                1,  # is_active
                datetime.now()
            ))
            
            conn.commit()
            student_id = cursor.lastrowid
            conn.close()
            
            # Reload student database
            self.reload_student_database()
            
            return {
                'success': True,
                'student_id': student_id,
                'face_confidence': faces[0]['confidence'],
                'embedding_quality': float(np.linalg.norm(embedding))
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def retrain_model(self):
        """Retrain model with current student data"""
        try:
            print("🎓 Retraining model with current student data...")
            
            # Load all student data
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, roll_number, photo_data
                FROM student 
                WHERE is_active = 1 AND photo_data IS NOT NULL
            ''')
            
            students = cursor.fetchall()
            conn.close()
            
            # Prepare training data
            student_data = []
            for student_id, name, roll_number, photo_data in students:
                student_data.append({
                    'id': student_id,
                    'name': name,
                    'roll_number': roll_number,
                    'photos': [photo_data]
                })
            
            # Train model
            training_results = self.face_recognizer.train_on_student_data(student_data)
            
            # Save trained model
            self.face_recognizer.save_model(self.model_path)
            
            # Reload student database with new embeddings
            self.reload_student_database()
            
            return {
                'success': True,
                'students_processed': training_results['students_processed'],
                'optimized_threshold': training_results['optimized_threshold']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Flask integration functions
def create_professional_attendance_routes(app, attendance_system):
    """Add professional attendance routes to Flask app"""
    
    @app.route('/api/professional_attendance', methods=['POST'])
    def professional_attendance():
        """Professional face recognition endpoint"""
        try:
            # Get image data
            if 'photo' in request.files:
                photo = request.files['photo']
                image_data = photo.read()
            elif request.json and 'image' in request.json:
                image_data = request.json['image']
            else:
                return jsonify({'success': False, 'error': 'No image provided'})
            
            # Process attendance
            results = attendance_system.process_attendance_image(image_data)
            
            return jsonify(results)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/add_professional_student', methods=['POST'])
    def add_professional_student():
        """Add student with professional face recognition"""
        try:
            # Get student data
            student_data = {
                'name': request.form.get('name'),
                'roll_number': request.form.get('roll_number'),
                'class_name': request.form.get('class_name', ''),
                'section': request.form.get('section', ''),
                'parent_name': request.form.get('parent_name', ''),
                'phone_number': request.form.get('phone_number', ''),
                'parent_phone': request.form.get('parent_phone', ''),
                'address': request.form.get('address', '')
            }
            
            # Get photo
            if 'photo' not in request.files:
                return jsonify({'success': False, 'error': 'Photo required'})
            
            photo = request.files['photo']
            photo_data = photo.read()
            
            # Add student
            result = attendance_system.add_student_with_photo(student_data, photo_data)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/retrain_model', methods=['POST'])
    def retrain_model():
        """Retrain face recognition model"""
        try:
            result = attendance_system.retrain_model()
            return jsonify(result)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    @app.route('/api/system_status', methods=['GET'])
    def system_status():
        """Get system status"""
        return jsonify({
            'students_in_database': len(attendance_system.student_database),
            'model_threshold': attendance_system.face_recognizer.similarity_threshold,
            'model_loaded': os.path.exists(attendance_system.model_path)
        })

# Standalone testing function
def test_professional_system():
    """Test the professional system with webcam"""
    print("🧪 Testing Professional Face Recognition System")
    print("Press SPACE to test recognition, 'r' to retrain, ESC to quit")
    
    # Initialize system
    attendance_system = ProfessionalAttendanceSystem()
    
    if not attendance_system.student_database:
        print("❌ No students in database. Please add students first.")
        return
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Display frame
        cv2.putText(frame, "SPACE: Test Recognition | R: Retrain | ESC: Quit", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow('Professional Face Recognition Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            # Test recognition
            print("\n🔍 Testing recognition...")
            results = attendance_system.process_attendance_image(frame)
            
            print(f"Results: {results['success']}")
            if results['success']:
                print(f"Total faces: {results['total_faces']}")
                print(f"Identified students: {results['identified_students']}")
                
                for student in results['results']:
                    print(f"  ✅ {student['student_name']} (Confidence: {student['similarity']:.3f})")
            else:
                print(f"Error: {results.get('error', 'Unknown error')}")
        
        elif key == ord('r'):
            # Retrain model
            print("\n🎓 Retraining model...")
            retrain_results = attendance_system.retrain_model()
            
            if retrain_results['success']:
                print(f"✅ Retraining complete!")
                print(f"Students processed: {retrain_results['students_processed']}")
                print(f"New threshold: {retrain_results['optimized_threshold']:.3f}")
            else:
                print(f"❌ Retraining failed: {retrain_results['error']}")
        
        elif key == 27:  # ESC
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_professional_system()