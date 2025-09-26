#!/usr/bin/env python3
"""
Debug face recognition step by step
"""

import sqlite3
import numpy as np
import cv2
import requests
import base64
from io import BytesIO
from PIL import Image

def debug_face_recognition():
    """Debug the entire face recognition pipeline"""
    print("🔍 Debugging Face Recognition Pipeline...")
    
    # Step 1: Check database students
    print("\n📊 Step 1: Checking database...")
    conn = sqlite3.connect('attendance_enhanced.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, roll_number, face_encoding FROM student WHERE is_active = 1 AND face_encoding IS NOT NULL')
    student_rows = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(student_rows)} students with face encodings:")
    for row in student_rows:
        try:
            encoding = np.frombuffer(row[3], dtype=np.float64)
            print(f"   ✅ {row[1]} ({row[2]}) - {len(encoding)} features")
            print(f"      Sample values: {encoding[:3]}")
        except Exception as e:
            print(f"   ❌ {row[1]} - Error: {e}")
    
    # Step 2: Capture test image
    print("\n📸 Step 2: Capturing test image...")
    print("Opening webcam... Press SPACE to capture, ESC to quit")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam")
        return
    
    test_image = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imshow('Capture Test Image - Press SPACE', frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            test_image = frame.copy()
            break
        elif key == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if test_image is None:
        print("❌ No image captured")
        return
    
    print("✅ Image captured")
    
    # Step 3: Send to Flask API
    print("\n🌐 Step 3: Testing Flask API...")
    
    # Convert image to bytes
    _, buffer = cv2.imencode('.jpg', test_image)
    image_bytes = buffer.tobytes()
    
    # Send to Flask endpoint
    try:
        files = {'photo': ('test.jpg', image_bytes, 'image/jpeg')}
        response = requests.post('http://127.0.0.1:5000/detect_and_identify_faces', files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response received")
            print(f"Success: {result.get('success', False)}")
            print(f"Message: {result.get('message', 'No message')}")
            
            if 'identified_faces' in result:
                faces = result['identified_faces']
                print(f"Faces detected: {len(faces)}")
                
                for i, face in enumerate(faces):
                    print(f"\n👤 Face {i+1}:")
                    print(f"   Bbox: {face.get('bbox', 'N/A')}")
                    print(f"   Confidence: {face.get('confidence', 'N/A')}")
                    print(f"   Similarity: {face.get('similarity', 'N/A')}")
                    print(f"   Identified: {face.get('identified', False)}")
                    
                    if face.get('student_info'):
                        student = face['student_info']
                        print(f"   Student: {student.get('name', 'N/A')} ({student.get('roll_number', 'N/A')})")
                    else:
                        print(f"   Student: No match")
            else:
                print("❌ No 'identified_faces' in response")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    debug_face_recognition()