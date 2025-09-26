#!/usr/bin/env python3
"""
Check students and their face encodings in the database
"""

import sqlite3
import json
import numpy as np

def check_students():
    """Check all students and their face encodings"""
    try:
        conn = sqlite3.connect('attendance_enhanced.db')
        cursor = conn.cursor()
        
        # Get all students (note: table name is 'student', not 'students')
        cursor.execute('SELECT id, name, email, phone, photo_filename, face_encoding FROM student')
        rows = cursor.fetchall()
        
        print(f"📊 Total students in database: {len(rows)}")
        print("-" * 60)
        
        for row in rows:
            student_id, name, email, phone, photo_filename, face_encoding = row
            print(f"👤 Student ID: {student_id}")
            print(f"   Name: {name}")
            print(f"   Email: {email}")
            print(f"   Phone: {phone}")
            print(f"   Photo: {photo_filename}")
            
            if face_encoding:
                try:
                    # Try to parse the face encoding
                    encoding_data = json.loads(face_encoding)
                    if isinstance(encoding_data, list):
                        encoding_array = np.array(encoding_data)
                        print(f"   ✅ Face Encoding: {len(encoding_array)} features")
                        print(f"   🔢 Encoding sample: {encoding_array[:5]}...")
                    else:
                        print(f"   ❌ Invalid face encoding format: {type(encoding_data)}")
                except json.JSONDecodeError as e:
                    print(f"   ❌ Face encoding JSON error: {e}")
                except Exception as e:
                    print(f"   ❌ Face encoding error: {e}")
            else:
                print(f"   ❌ No face encoding")
            
            print("-" * 60)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == '__main__':
    check_students()