"""
Direct database creation and test data insertion
"""
import sqlite3
import numpy as np
from datetime import date

def create_database_directly():
    """Create database and tables directly using sqlite3"""
    
    # Connect to database
    conn = sqlite3.connect('attendance_enhanced.db')
    cursor = conn.cursor()
    
    # Create students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            roll_number VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(100),
            phone VARCHAR(20),
            face_encoding BLOB,
            face_confidence FLOAT,
            photo_data BLOB,
            photo_filename VARCHAR(255),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            date DATE NOT NULL,
            time_in TIME,
            method VARCHAR(50) DEFAULT 'face_recognition',
            confidence_score FLOAT,
            photo_data BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student (id)
        )
    ''')
    
    # Create daily_code table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_code (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(10) NOT NULL,
            date DATE UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("✅ Tables created successfully")
    
    # Check if students exist
    cursor.execute('SELECT COUNT(*) FROM student')
    student_count = cursor.fetchone()[0]
    
    if student_count == 0:
        # Add test students with face encodings
        students_data = [
            ('John Doe', 'ST001', 'john.doe@school.com', '1234567890'),
            ('Jane Smith', 'ST002', 'jane.smith@school.com', '0987654321')
        ]
        
        for name, roll, email, phone in students_data:
            # Create a dummy face encoding (128 float32 values)
            dummy_encoding = np.random.rand(128).astype(np.float32)
            face_encoding_bytes = dummy_encoding.tobytes()
            
            cursor.execute('''
                INSERT INTO student (name, roll_number, email, phone, face_encoding, face_confidence, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, roll, email, phone, face_encoding_bytes, 0.85, True))
            
            print(f"➕ Added student: {name} ({roll})")
    
    # Add daily code for today
    today = date.today().isoformat()
    cursor.execute('SELECT COUNT(*) FROM daily_code WHERE date = ?', (today,))
    code_count = cursor.fetchone()[0]
    
    if code_count == 0:
        cursor.execute('''
            INSERT INTO daily_code (code, date, is_active)
            VALUES (?, ?, ?)
        ''', ('123456', today, True))
        print(f"📅 Added daily code for {today}: 123456")
    
    # Commit changes
    conn.commit()
    
    # Verify data
    cursor.execute('SELECT COUNT(*) FROM student')
    total_students = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM student WHERE face_encoding IS NOT NULL')
    students_with_encodings = cursor.fetchone()[0]
    
    print(f"📊 Total students: {total_students}")
    print(f"👤 Students with face encodings: {students_with_encodings}")
    
    # Show student details
    cursor.execute('SELECT id, name, roll_number FROM student')
    students = cursor.fetchall()
    for student in students:
        print(f"   - ID: {student[0]}, Name: {student[1]}, Roll: {student[2]}")
    
    conn.close()
    print("✅ Database setup completed!")

if __name__ == "__main__":
    create_database_directly()