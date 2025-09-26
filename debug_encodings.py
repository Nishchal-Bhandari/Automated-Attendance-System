#!/usr/bin/env python3
"""
Check students and their face encodings in the database (handle BLOB format)
"""

import sqlite3
import json
import numpy as np
import pickle

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
                    # Try different formats for face encoding
                    print(f"   📊 Face encoding type: {type(face_encoding)}")
                    print(f"   📊 Face encoding length: {len(face_encoding)} bytes")
                    
                    # Try to decode as JSON string first
                    if isinstance(face_encoding, str):
                        encoding_data = json.loads(face_encoding)
                        encoding_array = np.array(encoding_data)
                        print(f"   ✅ Face Encoding (JSON): {len(encoding_array)} features")
                        print(f"   🔢 Encoding sample: {encoding_array[:5]}...")
                    
                    # Try to decode as binary/BLOB
                    elif isinstance(face_encoding, bytes):
                        try:
                            # Try pickle first
                            encoding_array = pickle.loads(face_encoding)
                            print(f"   ✅ Face Encoding (Pickle): {len(encoding_array)} features")
                            print(f"   🔢 Encoding sample: {encoding_array[:5]}...")
                        except:
                            try:
                                # Try numpy array bytes
                                encoding_array = np.frombuffer(face_encoding, dtype=np.float64)
                                print(f"   ✅ Face Encoding (NumPy): {len(encoding_array)} features")
                                print(f"   🔢 Encoding sample: {encoding_array[:5]}...")
                            except:
                                try:
                                    # Try JSON from bytes
                                    encoding_str = face_encoding.decode('utf-8')
                                    encoding_data = json.loads(encoding_str)
                                    encoding_array = np.array(encoding_data)
                                    print(f"   ✅ Face Encoding (JSON from bytes): {len(encoding_array)} features")
                                    print(f"   🔢 Encoding sample: {encoding_array[:5]}...")
                                except:
                                    print(f"   ❌ Could not decode face encoding")
                                    print(f"   🔍 First 20 bytes: {face_encoding[:20]}")
                    
                except Exception as e:
                    print(f"   ❌ Face encoding error: {e}")
                    print(f"   🔍 First 20 bytes: {face_encoding[:20] if face_encoding else 'None'}")
            else:
                print(f"   ❌ No face encoding")
            
            print("-" * 60)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == '__main__':
    check_students()