"""
Add test students with face encodings to the database
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_enhanced_sql import app, db
from models_enhanced import Student, DailyCode
from datetime import date
import numpy as np

def add_test_students():
    """Add test students with dummy face encodings"""
    with app.app_context():
        try:
            # Create all tables first
            db.create_all()
            print("✅ Database tables created")
            
            # Check if students already exist
            existing_students = Student.query.count()
            if existing_students > 0:
                print(f"📊 Found {existing_students} existing students")
                return
            
            # Create test students
            students_data = [
                {
                    'name': 'John Doe',
                    'roll_number': 'ST001',
                    'email': 'john.doe@school.com',
                    'phone': '1234567890'
                },
                {
                    'name': 'Jane Smith', 
                    'roll_number': 'ST002',
                    'email': 'jane.smith@school.com',
                    'phone': '0987654321'
                }
            ]
            
            for student_data in students_data:
                # Create dummy face encoding (128-dimensional vector)
                dummy_encoding = np.random.rand(128).astype(np.float32)
                face_encoding_bytes = dummy_encoding.tobytes()
                
                student = Student(
                    name=student_data['name'],
                    roll_number=student_data['roll_number'],
                    email=student_data['email'],
                    phone=student_data['phone'],
                    face_encoding=face_encoding_bytes,
                    is_active=True
                )
                
                db.session.add(student)
                print(f"➕ Added student: {student_data['name']} ({student_data['roll_number']})")
            
            # Create daily code for today
            today = date.today()
            existing_code = DailyCode.query.filter_by(date=today).first()
            if not existing_code:
                daily_code = DailyCode(
                    code='123456',
                    date=today,
                    is_active=True
                )
                db.session.add(daily_code)
                print(f"📅 Created daily code for {today}: 123456")
            
            # Commit all changes
            db.session.commit()
            print("✅ Test data added successfully!")
            
            # Verify the data
            total_students = Student.query.count()
            students_with_encodings = Student.query.filter(Student.face_encoding.isnot(None)).count()
            print(f"📊 Total students: {total_students}")
            print(f"👤 Students with face encodings: {students_with_encodings}")
            
        except Exception as e:
            print(f"❌ Error adding test students: {e}")
            db.session.rollback()

if __name__ == "__main__":
    add_test_students()