#!/usr/bin/env python3
"""
Student Management Script
- Remove all student profiles from backend
- Clear attendance records
- Clean up uploaded photos
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_secure_rural import app, db, Student, Attendance

def remove_all_students():
    """Remove all student profiles and their data"""
    print("🗑️  Starting Student Profile Cleanup...")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Count existing data
            student_count = Student.query.count()
            attendance_count = Attendance.query.count()
            
            print(f"📊 Current Database Status:")
            print(f"   - Students: {student_count}")
            print(f"   - Attendance Records: {attendance_count}")
            
            if student_count == 0 and attendance_count == 0:
                print("✅ Database is already clean!")
                return
            
            # Remove all attendance records first (foreign key constraint)
            print(f"\n🗑️  Removing {attendance_count} attendance records...")
            Attendance.query.delete()
            db.session.commit()
            print("✅ All attendance records removed")
            
            # Get student photo paths before deletion
            students = Student.query.all()
            photo_paths = []
            
            print(f"\n🗑️  Removing {student_count} student profiles...")
            for student in students:
                if student.photo_path:
                    photo_paths.append(student.photo_path)
                print(f"   - Removing: {student.name} ({student.roll_number})")
            
            # Remove all students
            Student.query.delete()
            db.session.commit()
            print("✅ All student profiles removed")
            
            # Clean up photo files
            print(f"\n🗑️  Cleaning up {len(photo_paths)} photo files...")
            removed_photos = 0
            for photo_path in photo_paths:
                full_path = os.path.join("static", photo_path.lstrip('/'))
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                        removed_photos += 1
                        print(f"   - Removed: {photo_path}")
                    except Exception as e:
                        print(f"   - Error removing {photo_path}: {e}")
                else:
                    print(f"   - File not found: {photo_path}")
            
            print(f"✅ Removed {removed_photos} photo files")
            
            # Clean up empty directories
            uploads_dir = "static/uploads"
            if os.path.exists(uploads_dir):
                try:
                    # Remove empty subdirectories
                    for root, dirs, files in os.walk(uploads_dir, topdown=False):
                        for directory in dirs:
                            dir_path = os.path.join(root, directory)
                            try:
                                if not os.listdir(dir_path):  # Directory is empty
                                    os.rmdir(dir_path)
                                    print(f"   - Removed empty directory: {dir_path}")
                            except OSError:
                                pass  # Directory not empty or other error
                except Exception as e:
                    print(f"   - Error cleaning directories: {e}")
            
            # Verify cleanup
            final_student_count = Student.query.count()
            final_attendance_count = Attendance.query.count()
            
            print(f"\n📊 Final Database Status:")
            print(f"   - Students: {final_student_count}")
            print(f"   - Attendance Records: {final_attendance_count}")
            
            if final_student_count == 0 and final_attendance_count == 0:
                print("\n🎉 Student Profile Cleanup Completed Successfully!")
                print("   - All student profiles removed")
                print("   - All attendance records cleared")
                print("   - Photo files cleaned up")
                print("   - Database is now clean")
            else:
                print("\n⚠️  Warning: Some data may still remain")
                
        except Exception as e:
            print(f"\n❌ Error during cleanup: {e}")
            db.session.rollback()
            return False
    
    return True

def list_current_students():
    """List all current students in the database"""
    print("\n📋 Current Students in Database:")
    print("=" * 50)
    
    with app.app_context():
        students = Student.query.all()
        
        if not students:
            print("   No students found in database")
            return
        
        for i, student in enumerate(students, 1):
            print(f"{i}. {student.name}")
            print(f"   Roll Number: {student.roll_number}")
            print(f"   Parent: {student.parent_name}")
            print(f"   Phone: {student.phone_number}")
            print(f"   Registered: {student.created_at.strftime('%d %b %Y')}")
            if student.secure_token:
                print(f"   Secure Token: {student.secure_token[:10]}...")
            print()

if __name__ == "__main__":
    print("🎓 Student Management System")
    print("=" * 50)
    
    # List current students
    list_current_students()
    
    # Ask for confirmation
    response = input("\n⚠️  Do you want to remove ALL student profiles? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        success = remove_all_students()
        if success:
            print("\n🚀 You can now add new students through the web interface:")
            print("   1. Start the Flask app: python app_secure_rural.py")
            print("   2. Visit: http://127.0.0.1:5000")
            print("   3. Go to 'Add Student' to register new students")
    else:
        print("\n✅ Operation cancelled. No changes made to the database.")
        
    print("\n👋 Student management script completed.")