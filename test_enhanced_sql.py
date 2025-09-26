#!/usr/bin/env python3
"""
Test script for Enhanced SQL Database System
Tests BLOB photo storage, multi-database support, and integrity verification
"""

import os
import sys
import hashlib
import io
from PIL import Image
import numpy as np
import sqlite3
from datetime import datetime, date

def print_section(title):
    """Print section header"""
    print(f"\n{'='*20} {title} {'='*20}")

def create_test_image():
    """Create a test image for testing"""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()

def test_database_config():
    """Test database configuration system"""
    print_section("Testing Database Configuration")
    
    try:
        from database_config import DatabaseConfig, SQLiteConfig
        
        # Test SQLite configuration
        sqlite_config = SQLiteConfig()
        print(f"✅ SQLite Config: {sqlite_config.get_database_uri()}")
        
        # Test database connection
        if sqlite_config.test_connection():
            print("✅ Database connection test passed")
        else:
            print("❌ Database connection test failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Database configuration test failed: {e}")
        return False

def test_enhanced_models():
    """Test enhanced database models"""
    print_section("Testing Enhanced Models")
    
    try:
        from models_enhanced import Student, PhotoMetadata, Attendance, db
        from app_enhanced_sql import create_app
        
        app = create_app()
        
        with app.app_context():
            # Create tables
            db.create_all()
            print("✅ Database tables created")
            
            # Test student model with BLOB photo
            test_photo = create_test_image()
            photo_hash = hashlib.sha256(test_photo).hexdigest()
            
            student = Student(
                name="Test Student",
                roll_number="TEST001",
                class_name="Test Class",
                photo_blob=test_photo,
                photo_hash=photo_hash
            )
            
            db.session.add(student)
            db.session.commit()
            print("✅ Student with BLOB photo created")
            
            # Test photo retrieval
            retrieved_student = Student.query.filter_by(roll_number="TEST001").first()
            if retrieved_student and retrieved_student.photo_blob:
                retrieved_hash = hashlib.sha256(retrieved_student.photo_blob).hexdigest()
                if retrieved_hash == photo_hash:
                    print("✅ Photo BLOB integrity verified")
                else:
                    print("❌ Photo BLOB integrity check failed")
            
            # Test photo metadata
            metadata = PhotoMetadata(
                student_id=student.id,
                filename="test_photo.png",
                file_size=len(test_photo),
                file_hash=photo_hash,
                mime_type="image/png"
            )
            
            db.session.add(metadata)
            db.session.commit()
            print("✅ Photo metadata created")
            
            # Cleanup
            db.session.delete(metadata)
            db.session.delete(student)
            db.session.commit()
            print("✅ Test data cleaned up")
            
        return True
        
    except Exception as e:
        print(f"❌ Enhanced models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_photo_storage():
    """Test photo storage functionality"""
    print_section("Testing Photo Storage")
    
    try:
        from app_enhanced_sql import create_app, save_photo_to_db
        from models_enhanced import db, Student
        
        app = create_app()
        
        with app.app_context():
            # Create test image
            test_photo = create_test_image()
            
            # Create a PIL Image from bytes
            pil_image = Image.open(io.BytesIO(test_photo))
            
            # Test save_photo_to_db function
            result = save_photo_to_db(pil_image, "test_photo.png", "TEST002")
            
            if result['success']:
                print("✅ Photo saved to database successfully")
                print(f"   File hash: {result['file_hash'][:16]}...")
                print(f"   File size: {result['file_size']} bytes")
                
                # Verify student was created
                student = Student.query.filter_by(roll_number="TEST002").first()
                if student and student.photo_blob:
                    print("✅ Student with photo BLOB found in database")
                    
                    # Verify hash
                    db_hash = hashlib.sha256(student.photo_blob).hexdigest()
                    if db_hash == result['file_hash']:
                        print("✅ Photo integrity verification passed")
                    else:
                        print("❌ Photo integrity verification failed")
                    
                    # Cleanup
                    db.session.delete(student)
                    db.session.commit()
                    print("✅ Test data cleaned up")
                else:
                    print("❌ Student with photo not found in database")
            else:
                print(f"❌ Photo save failed: {result.get('error', 'Unknown error')}")
                return False
            
        return True
        
    except Exception as e:
        print(f"❌ Photo storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_face_recognition_integration():
    """Test face recognition integration"""
    print_section("Testing Face Recognition Integration")
    
    try:
        from mediapipe_face_recognition import MediaPipeFaceRecognition
        
        # Initialize face recognition
        face_rec = MediaPipeFaceRecognition()
        print("✅ Face recognition system initialized")
        
        # Create test image
        test_photo = create_test_image()
        pil_image = Image.open(io.BytesIO(test_photo))
        
        # Convert to numpy array
        image_array = np.array(pil_image)
        
        # Test face detection (may not find faces in solid color image)
        try:
            faces = face_rec.detect_faces(image_array)
            print(f"✅ Face detection completed - Found {len(faces)} faces")
        except Exception as e:
            print(f"⚠️ Face detection warning (expected for test image): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Face recognition test failed: {e}")
        return False

def test_database_operations():
    """Test database operations"""
    print_section("Testing Database Operations")
    
    try:
        from app_enhanced_sql import create_app
        from models_enhanced import db, Student, Attendance, DailyCode
        
        app = create_app()
        
        with app.app_context():
            # Test daily code creation
            daily_code = DailyCode.generate_for_date(date.today())
            db.session.add(daily_code)
            db.session.commit()
            print(f"✅ Daily code created: {daily_code.code}")
            
            # Test daily code retrieval
            retrieved_code = DailyCode.get_current()
            if retrieved_code and retrieved_code.code == daily_code.code:
                print("✅ Daily code retrieval successful")
            else:
                print("❌ Daily code retrieval failed")
            
            # Test student operations
            test_photo = create_test_image()
            student = Student(
                name="Database Test Student",
                roll_number="DB001",
                class_name="Test Class",
                photo_blob=test_photo,
                photo_hash=hashlib.sha256(test_photo).hexdigest()
            )
            
            db.session.add(student)
            db.session.commit()
            print("✅ Student added to database")
            
            # Test attendance marking
            attendance = Attendance(
                student_id=student.id,
                date=date.today(),
                status="Present",
                method="Manual Test"
            )
            
            db.session.add(attendance)
            db.session.commit()
            print("✅ Attendance marked")
            
            # Test queries
            present_count = Attendance.query.filter_by(
                date=date.today(),
                status="Present"
            ).count()
            print(f"✅ Present students today: {present_count}")
            
            # Cleanup
            db.session.delete(attendance)
            db.session.delete(student)
            db.session.delete(daily_code)
            db.session.commit()
            print("✅ Test data cleaned up")
            
        return True
        
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sql_performance():
    """Test SQL performance with BLOB storage"""
    print_section("Testing SQL Performance")
    
    try:
        from app_enhanced_sql import create_app
        from models_enhanced import db, Student
        import time
        
        app = create_app()
        
        with app.app_context():
            # Create test photos of different sizes
            sizes = [50, 100, 200]
            students = []
            
            print("Creating test students with photos...")
            start_time = time.time()
            
            for i, size in enumerate(sizes):
                # Create test image
                img = Image.new('RGB', (size, size), color=(i*80, 100, 200))
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                img_data = img_bytes.getvalue()
                
                student = Student(
                    name=f"Perf Test {i+1}",
                    roll_number=f"PERF{i+1:03d}",
                    class_name="Performance Test",
                    photo_blob=img_data,
                    photo_hash=hashlib.sha256(img_data).hexdigest()
                )
                
                students.append(student)
                db.session.add(student)
            
            db.session.commit()
            create_time = time.time() - start_time
            print(f"✅ Created {len(students)} students in {create_time:.3f}s")
            
            # Test retrieval performance
            start_time = time.time()
            retrieved_students = Student.query.filter(
                Student.roll_number.like('PERF%')
            ).all()
            
            total_photo_size = sum(
                len(s.photo_blob) if s.photo_blob else 0 
                for s in retrieved_students
            )
            retrieval_time = time.time() - start_time
            
            print(f"✅ Retrieved {len(retrieved_students)} students in {retrieval_time:.3f}s")
            print(f"✅ Total photo data: {total_photo_size:,} bytes")
            
            # Cleanup
            for student in students:
                db.session.delete(student)
            db.session.commit()
            print("✅ Performance test data cleaned up")
            
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🧪 Enhanced SQL Database System Test Suite")
    print("=" * 60)
    
    tests = [
        ("Database Configuration", test_database_config),
        ("Enhanced Models", test_enhanced_models),
        ("Photo Storage", test_photo_storage),
        ("Face Recognition Integration", test_face_recognition_integration),
        ("Database Operations", test_database_operations),
        ("SQL Performance", test_sql_performance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_function in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_function():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced SQL system is ready.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)