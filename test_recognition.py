#!/usr/bin/env python3
"""
Test face recognition with actual students in database
"""

import sqlite3
import numpy as np
import cv2
import os
from mediapipe_face_recognition import MediaPipeFaceRecognition

def test_face_recognition():
    """Test face recognition against database students"""
    print("🔍 Testing Face Recognition System...")
    
    # Initialize face recognition
    face_rec = MediaPipeFaceRecognition()
    
    # Load students from database
    conn = sqlite3.connect('attendance_enhanced.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, roll_number, face_encoding FROM student WHERE is_active = 1 AND face_encoding IS NOT NULL')
    student_rows = cursor.fetchall()
    conn.close()
    
    print(f"📊 Found {len(student_rows)} students with face encodings")
    
    # Prepare known faces
    known_faces = []
    for row in student_rows:
        try:
            encoding = np.frombuffer(row[3], dtype=np.float64)  # Fixed: use float64
            known_faces.append({
                'id': row[0],
                'name': row[1],
                'roll_number': row[2],
                'encoding': encoding
            })
            print(f"   ✅ Loaded: {row[1]} ({row[2]}) - Encoding: {len(encoding)} features")
        except Exception as e:
            print(f"   ❌ Failed to load {row[1]}: {e}")
    
    print(f"\n🎯 Ready to test with {len(known_faces)} known faces")
    
    # Test with webcam or saved image
    test_image_path = input("\nEnter path to test image (or press Enter for webcam): ").strip()
    
    if test_image_path and os.path.exists(test_image_path):
        # Test with image file
        image = cv2.imread(test_image_path)
        if image is None:
            print("❌ Could not load image")
            return
        
        print(f"📸 Testing with image: {test_image_path}")
        
    else:
        # Test with webcam
        print("📹 Opening webcam... Press SPACE to capture, ESC to quit")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Could not open webcam")
            return
        
        image = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            cv2.imshow('Face Recognition Test - Press SPACE to capture', frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):  # Space to capture
                image = frame.copy()
                break
            elif key == 27:  # ESC to quit
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if image is None:
            print("❌ No image captured")
            return
    
    # Perform face recognition
    print("\n🔍 Analyzing image...")
    identified_faces = face_rec.identify_faces(image, known_faces)
    
    print(f"📊 Results: {len(identified_faces)} faces detected")
    
    for i, face in enumerate(identified_faces):
        print(f"\n👤 Face {i+1}:")
        print(f"   Confidence: {face['confidence']:.2f}")
        print(f"   Similarity: {face['similarity']:.2f}")
        print(f"   Identified: {face['identified']}")
        
        if face['identified'] and face['student_info']:
            student = face['student_info']
            print(f"   ✅ Matched: {student['name']} ({student['roll_number']})")
        else:
            print(f"   ❌ No match found")
    
    # Display results
    if len(identified_faces) > 0:
        result_image = image.copy()
        
        for face in identified_faces:
            x, y, w, h = face['bbox']
            
            if face['identified']:
                # Green box for identified
                cv2.rectangle(result_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                student = face['student_info']
                label = f"{student['name']} ({face['similarity']:.2f})"
                cv2.putText(result_image, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            else:
                # Red box for unidentified
                cv2.rectangle(result_image, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(result_image, "Unknown", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        cv2.imshow('Face Recognition Results - Press any key to close', result_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == '__main__':
    test_face_recognition()