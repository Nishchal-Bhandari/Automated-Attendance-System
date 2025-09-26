"""
Demo script to create sample students for testing
Run this after setting up the application to add test data
"""

from app import app, db, Student
import os
import json
import face_recognition
from datetime import datetime

def create_sample_students():
    """Create sample students for testing"""
    
    # Sample student data
    sample_students = [
        {
            'name': 'Rajesh Kumar',
            'roll_number': 'STU001',
        },
        {
            'name': 'Priya Sharma',
            'roll_number': 'STU002',
        },
        {
            'name': 'Arjun Singh',
            'roll_number': 'STU003',
        },
        {
            'name': 'Meera Patel',
            'roll_number': 'STU004',
        },
        {
            'name': 'Kiran Joshi',
            'roll_number': 'STU005',
        }
    ]
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        print("Creating sample students...")
        
        for student_data in sample_students:
            # Check if student already exists
            existing = Student.query.filter_by(roll_number=student_data['roll_number']).first()
            if existing:
                print(f"Student {student_data['name']} already exists. Skipping...")
                continue
            
            # Create student without photo for now
            # In real usage, photos would be uploaded through the web interface
            student = Student(
                name=student_data['name'],
                roll_number=student_data['roll_number'],
                photo_path='static/uploads/placeholder.jpg',  # Placeholder path
                face_encoding=None,  # Will be set when photo is uploaded
                created_at=datetime.utcnow()
            )
            
            db.session.add(student)
            print(f"Added student: {student_data['name']} ({student_data['roll_number']})")
        
        db.session.commit()
        print("\nSample students created successfully!")
        print("You can now:")
        print("1. Start the server with: python app.py")
        print("2. Go to http://localhost:5000")
        print("3. Add photos for students to enable face recognition")
        print("4. Test the attendance marking feature")

if __name__ == '__main__':
    create_sample_students()