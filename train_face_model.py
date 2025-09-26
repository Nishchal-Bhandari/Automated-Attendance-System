"""
Professional Model Training Script for Student Attendance System
Trains face recognition models on student photos for optimal performance
"""

import os
import sys
import sqlite3
import cv2
import numpy as np
from professional_face_recognition import ProfessionalFaceRecognizer
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd

class StudentAttendanceModelTrainer:
    """
    Professional model trainer for student attendance system
    """
    
    def __init__(self, db_path='attendance_enhanced.db'):
        self.db_path = db_path
        self.face_recognizer = ProfessionalFaceRecognizer()
        self.training_data = []
        self.validation_data = []
        self.student_embeddings = {}
        
    def load_student_data(self):
        """Load all student photos from database"""
        print("📊 Loading student data from database...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all active students with photos
            cursor.execute('''
                SELECT id, name, roll_number, photo_data, face_encoding
                FROM student 
                WHERE is_active = 1 AND photo_data IS NOT NULL
            ''')
            
            students = cursor.fetchall()
            print(f"Found {len(students)} students with photos")
            
            student_data = []
            for student_id, name, roll_number, photo_data, face_encoding in students:
                student_info = {
                    'id': student_id,
                    'name': name,
                    'roll_number': roll_number,
                    'photos': [photo_data]  # Can be extended for multiple photos
                }
                student_data.append(student_info)
            
            conn.close()
            return student_data
            
        except Exception as e:
            print(f"❌ Error loading student data: {e}")
            return []
    
    def augment_training_data(self, student_data):
        """
        Augment training data with variations of student photos
        """
        print("🔄 Augmenting training data...")
        
        augmented_data = []
        
        for student in student_data:
            original_photos = student['photos']
            augmented_photos = []
            
            for photo_data in original_photos:
                # Decode image
                image = cv2.imdecode(np.frombuffer(photo_data, np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    continue
                
                # Original image
                augmented_photos.append(cv2.imencode('.jpg', image)[1].tobytes())
                
                # Augmentations
                augmentations = [
                    self._rotate_image(image, 5),   # Slight rotation
                    self._rotate_image(image, -5),
                    self._adjust_brightness(image, 1.2),  # Brighter
                    self._adjust_brightness(image, 0.8),  # Darker
                    self._add_noise(image),               # Noise
                    self._blur_image(image),              # Slight blur
                ]
                
                for aug_image in augmentations:
                    if aug_image is not None:
                        augmented_photos.append(cv2.imencode('.jpg', aug_image)[1].tobytes())
            
            # Update student data with augmented photos
            student['photos'] = augmented_photos
            augmented_data.append(student)
        
        print(f"✅ Data augmentation complete. Average {len(augmented_data[0]['photos'])} photos per student")
        return augmented_data
    
    def _rotate_image(self, image, angle):
        """Rotate image by angle degrees"""
        try:
            h, w = image.shape[:2]
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            return cv2.warpAffine(image, matrix, (w, h))
        except:
            return None
    
    def _adjust_brightness(self, image, factor):
        """Adjust image brightness"""
        try:
            return cv2.convertScaleAbs(image, alpha=factor, beta=0)
        except:
            return None
    
    def _add_noise(self, image):
        """Add Gaussian noise to image"""
        try:
            noise = np.random.normal(0, 25, image.shape).astype(np.uint8)
            return cv2.add(image, noise)
        except:
            return None
    
    def _blur_image(self, image):
        """Apply slight Gaussian blur"""
        try:
            return cv2.GaussianBlur(image, (3, 3), 0)
        except:
            return None
    
    def train_model(self, student_data, augment_data=True):
        """
        Train the face recognition model on student data
        """
        print("🎓 Starting model training...")
        
        # Augment data if requested
        if augment_data:
            student_data = self.augment_training_data(student_data)
        
        # Train the model
        training_results = self.face_recognizer.train_on_student_data(student_data)
        
        # Save training results
        self._save_training_results(training_results)
        
        return training_results
    
    def validate_model(self, student_data):
        """
        Validate the trained model performance
        """
        print("🧪 Validating model performance...")
        
        validation_results = {
            'total_tests': 0,
            'correct_identifications': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1_score': 0.0
        }
        
        # Load student database for testing
        student_db = self._create_student_database(student_data)
        
        true_labels = []
        predicted_labels = []
        
        for student in student_data:
            student_id = student['id']
            student_name = student['name']
            
            # Test with each photo
            for i, photo_data in enumerate(student['photos']):
                # Skip some photos for validation (use every 3rd photo)
                if i % 3 != 0:
                    continue
                
                image = cv2.imdecode(np.frombuffer(photo_data, np.uint8), cv2.IMREAD_COLOR)
                if image is None:
                    continue
                
                # Identify student
                results = self.face_recognizer.identify_student(image, student_db)
                
                validation_results['total_tests'] += 1
                true_labels.append(student_name)
                
                if results and results[0]['identified']:
                    predicted_name = results[0]['student_info']['name']
                    predicted_labels.append(predicted_name)
                    
                    if predicted_name == student_name:
                        validation_results['correct_identifications'] += 1
                    else:
                        validation_results['false_positives'] += 1
                else:
                    predicted_labels.append('Unknown')
                    validation_results['false_negatives'] += 1
        
        # Calculate metrics
        if validation_results['total_tests'] > 0:
            validation_results['accuracy'] = validation_results['correct_identifications'] / validation_results['total_tests']
        
        # Generate detailed report
        if true_labels and predicted_labels:
            report = classification_report(true_labels, predicted_labels, output_dict=True, zero_division=0)
            validation_results['detailed_report'] = report
        
        print(f"✅ Validation complete:")
        print(f"   Accuracy: {validation_results['accuracy']:.3f}")
        print(f"   Total tests: {validation_results['total_tests']}")
        print(f"   Correct: {validation_results['correct_identifications']}")
        print(f"   False positives: {validation_results['false_positives']}")
        print(f"   False negatives: {validation_results['false_negatives']}")
        
        return validation_results
    
    def _create_student_database(self, student_data):
        """Create student database for validation"""
        student_db = []
        
        for student in student_data:
            # Use first photo for database entry
            if student['photos']:
                photo_data = student['photos'][0]
                image = cv2.imdecode(np.frombuffer(photo_data, np.uint8), cv2.IMREAD_COLOR)
                
                faces = self.face_recognizer.detect_faces(image)
                if faces:
                    embedding = self.face_recognizer.generate_ensemble_embedding(faces[0]['face_region'])
                    if embedding is not None:
                        student_db.append({
                            'id': student['id'],
                            'name': student['name'],
                            'roll_number': student['roll_number'],
                            'embedding': embedding
                        })
        
        return student_db
    
    def _save_training_results(self, results):
        """Save training results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_results_{timestamp}.json"
        
        # Convert numpy arrays to lists for JSON serialization
        json_results = {}
        for key, value in results.items():
            if key == 'student_embeddings':
                json_results[key] = {
                    student_id: {
                        'id': data['id'],
                        'name': data['name'],
                        'num_photos': data['num_photos']
                        # Skip embedding for JSON
                    }
                    for student_id, data in value.items()
                }
            else:
                json_results[key] = value
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        print(f"💾 Training results saved to {filename}")
    
    def generate_performance_report(self, validation_results):
        """Generate visual performance report"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Create performance visualization
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Face Recognition Model Performance Report', fontsize=16)
            
            # 1. Accuracy metrics
            metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
            values = [
                validation_results.get('accuracy', 0),
                validation_results.get('precision', 0),
                validation_results.get('recall', 0),
                validation_results.get('f1_score', 0)
            ]
            
            axes[0, 0].bar(metrics, values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
            axes[0, 0].set_title('Performance Metrics')
            axes[0, 0].set_ylim(0, 1)
            axes[0, 0].set_ylabel('Score')
            
            # 2. Confusion matrix (if available)
            if 'detailed_report' in validation_results:
                # Simplified confusion matrix visualization
                correct = validation_results['correct_identifications']
                fp = validation_results['false_positives']
                fn = validation_results['false_negatives']
                
                confusion_data = np.array([[correct, fp], [fn, 0]])
                sns.heatmap(confusion_data, annot=True, fmt='d', ax=axes[0, 1],
                           xticklabels=['Predicted Positive', 'Predicted Negative'],
                           yticklabels=['Actual Positive', 'Actual Negative'])
                axes[0, 1].set_title('Confusion Matrix')
            
            # 3. Test distribution
            total_tests = validation_results['total_tests']
            correct_ids = validation_results['correct_identifications']
            incorrect = total_tests - correct_ids
            
            axes[1, 0].pie([correct_ids, incorrect], labels=['Correct', 'Incorrect'],
                          autopct='%1.1f%%', colors=['#2ca02c', '#d62728'])
            axes[1, 0].set_title('Identification Results')
            
            # 4. Model statistics
            stats_text = f"""
            Total Students: {validation_results.get('students_processed', 'N/A')}
            Total Tests: {total_tests}
            Correct Identifications: {correct_ids}
            False Positives: {fp}
            False Negatives: {fn}
            Model Accuracy: {validation_results['accuracy']:.3f}
            """
            
            axes[1, 1].text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center',
                           transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('Model Statistics')
            axes[1, 1].axis('off')
            
            plt.tight_layout()
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"performance_report_{timestamp}.png"
            plt.savefig(report_filename, dpi=300, bbox_inches='tight')
            plt.show()
            
            print(f"📊 Performance report saved as {report_filename}")
            
        except ImportError:
            print("⚠️ Matplotlib/Seaborn not available. Skipping visual report.")
        except Exception as e:
            print(f"❌ Error generating report: {e}")
    
    def update_database_with_embeddings(self, training_results):
        """Update database with optimized embeddings"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            student_embeddings = training_results.get('student_embeddings', {})
            
            for student_id, student_data in student_embeddings.items():
                embedding_bytes = student_data['embedding'].astype(np.float32).tobytes()
                
                cursor.execute('''
                    UPDATE student 
                    SET face_encoding = ?, face_confidence = ?
                    WHERE id = ?
                ''', (embedding_bytes, 0.95, student_id))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Database updated with {len(student_embeddings)} optimized embeddings")
            
        except Exception as e:
            print(f"❌ Database update error: {e}")

def main():
    """Main training pipeline"""
    print("🚀 Professional Face Recognition Model Training")
    print("=" * 50)
    
    # Initialize trainer
    trainer = StudentAttendanceModelTrainer()
    
    # Load student data
    print("\n1. Loading student data...")
    student_data = trainer.load_student_data()
    
    if not student_data:
        print("❌ No student data found. Please add students with photos first.")
        return
    
    print(f"✅ Loaded {len(student_data)} students")
    
    # Train model
    print("\n2. Training model...")
    training_results = trainer.train_model(student_data, augment_data=True)
    
    if not training_results:
        print("❌ Training failed.")
        return
    
    print(f"✅ Training complete!")
    print(f"   Students processed: {training_results['students_processed']}")
    print(f"   Total embeddings: {training_results['total_embeddings']}")
    print(f"   Optimized threshold: {training_results['optimized_threshold']:.3f}")
    
    # Validate model
    print("\n3. Validating model...")
    validation_results = trainer.validate_model(student_data)
    
    # Generate performance report
    print("\n4. Generating performance report...")
    trainer.generate_performance_report(validation_results)
    
    # Update database
    print("\n5. Updating database...")
    trainer.update_database_with_embeddings(training_results)
    
    # Save trained model
    print("\n6. Saving trained model...")
    trainer.face_recognizer.save_model('trained_face_model.pkl')
    
    print("\n✅ Training pipeline complete!")
    print(f"   Final model accuracy: {validation_results['accuracy']:.3f}")
    print("   Model ready for production use!")

if __name__ == "__main__":
    main()