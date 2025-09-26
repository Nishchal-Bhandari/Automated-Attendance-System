#!/usr/bin/env python3
"""
Simple face encoding regeneration
"""

import sqlite3
import numpy as np

def fix_encodings():
    """Fix existing face encodings by converting from float64 to float32"""
    print("🔄 Converting existing face encodings...")
    
    conn = sqlite3.connect('attendance_enhanced.db')
    cursor = conn.cursor()
    
    # Get all students with face encodings
    cursor.execute('SELECT id, name, face_encoding FROM student WHERE face_encoding IS NOT NULL')
    students = cursor.fetchall()
    
    print(f"📊 Found {len(students)} students with encodings")
    
    for student_id, name, face_encoding in students:
        try:
            # Try to read as float64 (old format)
            old_encoding = np.frombuffer(face_encoding, dtype=np.float64)
            print(f"👤 {name}: Converting {len(old_encoding)} features from float64 to float32")
            
            # Convert to float32
            new_encoding = old_encoding.astype(np.float32)
            new_bytes = new_encoding.tobytes()
            
            # Update in database
            cursor.execute('UPDATE student SET face_encoding = ? WHERE id = ?', (new_bytes, student_id))
            
            print(f"   ✅ Converted: {len(new_encoding)} features, {len(new_bytes)} bytes")
            
        except Exception as e:
            print(f"   ❌ Error converting {name}: {e}")
    
    conn.commit()
    
    # Verify
    print("\n🔍 Verifying conversions...")
    cursor.execute('SELECT id, name, face_encoding FROM student WHERE face_encoding IS NOT NULL')
    students = cursor.fetchall()
    
    for student_id, name, face_encoding in students:
        try:
            encoding = np.frombuffer(face_encoding, dtype=np.float32)
            print(f"   ✅ {name}: {len(encoding)} features (float32)")
        except Exception as e:
            print(f"   ❌ {name}: Error - {e}")
    
    conn.close()
    print("\n✅ Conversion complete!")

if __name__ == '__main__':
    fix_encodings()