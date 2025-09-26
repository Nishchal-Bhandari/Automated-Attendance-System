#!/usr/bin/env python3
"""
Test face recognition with a simple API call
"""

import requests
import cv2
import numpy as np
import time

def test_face_recognition():
    """Test the face recognition API"""
    print("🧪 Testing Face Recognition API...")
    
    # Create a simple test with webcam
    print("📹 Opening webcam for test... Press SPACE to test recognition")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open webcam")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Show preview
        cv2.putText(frame, "Press SPACE to test face recognition", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow('Face Recognition Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):  # Space to test
            print("\n🔍 Capturing and testing...")
            
            # Encode image
            _, buffer = cv2.imencode('.jpg', frame)
            image_bytes = buffer.tobytes()
            
            # Send to API
            try:
                files = {'photo': ('test.jpg', image_bytes, 'image/jpeg')}
                response = requests.post('http://127.0.0.1:5000/detect_and_identify_faces', 
                                       files=files, timeout=10)
                
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"Success: {result.get('success')}")
                    
                    if result.get('identified_faces'):
                        faces = result['identified_faces']
                        print(f"🎯 Found {len(faces)} faces:")
                        
                        for i, face in enumerate(faces):
                            print(f"  Face {i+1}:")
                            print(f"    Confidence: {face.get('confidence', 0):.3f}")
                            print(f"    Similarity: {face.get('similarity', 0):.3f}")
                            print(f"    Identified: {face.get('identified', False)}")
                            
                            if face.get('student_info'):
                                student = face['student_info']
                                print(f"    ✅ Student: {student.get('name')} ({student.get('roll_number')})")
                            else:
                                print(f"    ❌ No match found")
                    else:
                        print("❌ No faces detected")
                else:
                    print(f"❌ Error: {response.text}")
                    
            except Exception as e:
                print(f"❌ API call failed: {e}")
                
        elif key == 27:  # ESC to quit
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    test_face_recognition()