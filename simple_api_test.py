#!/usr/bin/env python3
"""
Simple test to call the face recognition API
"""

import requests
import cv2
import numpy as np

def test_api():
    """Test the face recognition API with a simple image"""
    print("🔍 Testing Face Recognition API...")
    
    # Create a simple test image with webcam
    print("📹 Opening webcam... Press SPACE to capture")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Could not open webcam")
        return
    
    image = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imshow('Press SPACE to capture for API test', frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            image = frame.copy()
            break
        elif key == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if image is None:
        print("No image captured")
        return
    
    # Convert to bytes
    _, buffer = cv2.imencode('.jpg', image)
    image_bytes = buffer.tobytes()
    
    # Send to API
    print("🌐 Sending to Flask API...")
    try:
        files = {'photo': ('test.jpg', image_bytes, 'image/jpeg')}
        response = requests.post('http://127.0.0.1:5000/detect_and_identify_faces', files=files)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_api()