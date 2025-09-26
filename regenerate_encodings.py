#!/usr/bin/env python3
"""
Regenerate face encodings for all students with correct data type
"""

import sqlite3
import numpy as np
from PIL import Image
import io
from mediapipe_face_recognition import MediaPipeFaceRecognition

def regenerate_face_encodings():
    """Regenerate face encodings for all students"""
    print("🔄 Regenerating Face Encodings...")
    
    # Initialize face recognition
    face_rec = MediaPipeFaceRecognition()
    
    # Connect to database
    conn = sqlite3.connect('attendance_enhanced.db')
    cursor = conn.cursor()
    
    # Get all students with photos
    cursor.execute('SELECT id, name, photo_data FROM student WHERE photo_data IS NOT NULL')
    students = cursor.fetchall()
    
    print(f"📊 Found {len(students)} students with photos")
    
    for student_id, name, photo_data in students:
        try:
            print(f"\n👤 Processing {name} (ID: {student_id})...")
            
            # Convert BLOB to image
            image = Image.open(io.BytesIO(photo_data))
            image_array = np.array(image)
            
            # Convert to RGB if needed
            if len(image_array.shape) == 3 and image_array.shape[2] == 4:  # RGBA
                image_array = image_array[:, :, :3]  # Remove alpha channel
            
            print(f"   📸 Image shape: {image_array.shape}")
            
            # Detect faces
            faces = face_rec.detect_faces(image_array)
            print(f"   🔍 Detected {len(faces)} faces")
            
            if faces:
                # Generate encoding for the first face
                encoding = face_rec.generate_face_encoding(faces[0]['face_region'])
                
                if encoding is not None:
                    print(f"   ✅ Generated encoding: {encoding.shape}, dtype: {encoding.dtype}")
                    
                    # Store in database (ensure it's float32)
                    encoding_bytes = encoding.astype(np.float32).tobytes()
                    cursor.execute(
                        'UPDATE student SET face_encoding = ? WHERE id = ?',
                        (encoding_bytes, student_id)
                    )
                    
                    print(f"   💾 Stored encoding ({len(encoding_bytes)} bytes)")
                else:
                    print(f"   ❌ Failed to generate encoding")
            else:
                print(f"   ❌ No faces detected in photo")
                
        except Exception as e:
            print(f"   ❌ Error processing {name}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n✅ Face encoding regeneration complete!")
    
    # Verify the results
    print("\n🔍 Verifying results...")
    conn = sqlite3.connect('attendance_enhanced.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, face_encoding FROM student WHERE face_encoding IS NOT NULL')
    results = cursor.fetchall()
    
    for student_id, name, face_encoding in results:
        try:
            encoding = np.frombuffer(face_encoding, dtype=np.float32)
            print(f"   ✅ {name}: {len(encoding)} features, range: [{encoding.min():.3f}, {encoding.max():.3f}]")
        except Exception as e:
            print(f"   ❌ {name}: Error reading encoding - {e}")
    
    conn.close()

if __name__ == '__main__':
    regenerate_face_encodings()