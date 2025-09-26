"""
Secure Rural School Attendance System Demo
This script demonstrates the secure alternatives without RFID
"""

from app_secure_rural import app, db, Student, Attendance, DailyCode, generate_daily_code
import os
from datetime import datetime, date

def create_rural_demo_data():
    """Create sample data for rural school testing"""
    
    # Sample rural school students (Indian names)
    rural_students = [
        {
            'name': 'Aarav Sharma',
            'roll_number': 'RS001',
            'parent_name': 'Rajesh Sharma',
            'phone_number': '9876543210'
        },
        {
            'name': 'Kavya Patel',
            'roll_number': 'RS002',
            'parent_name': 'Suresh Patel',
            'phone_number': '9876543211'
        },
        {
            'name': 'Arjun Singh',
            'roll_number': 'RS003',
            'parent_name': 'Vikram Singh',
            'phone_number': '9876543212'
        },
        {
            'name': 'Priya Gupta',
            'roll_number': 'RS004',
            'parent_name': 'Amit Gupta',
            'phone_number': '9876543213'
        },
        {
            'name': 'Rohit Kumar',
            'roll_number': 'RS005',
            'parent_name': 'Manoj Kumar',
            'phone_number': '9876543214'
        },
        {
            'name': 'Ananya Joshi',
            'roll_number': 'RS006',
            'parent_name': 'Prakash Joshi',
            'phone_number': '9876543215'
        },
        {
            'name': 'Karan Mehta',
            'roll_number': 'RS007',
            'parent_name': 'Ravi Mehta',
            'phone_number': '9876543216'
        },
        {
            'name': 'Sneha Yadav',
            'roll_number': 'RS008',
            'parent_name': 'Sunil Yadav',
            'phone_number': '9876543217'
        }
    ]
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        print("🏫 Creating Rural School Demo Data...")
        print("=" * 50)
        
        for student_data in rural_students:
            # Check if student already exists
            existing = Student.query.filter_by(roll_number=student_data['roll_number']).first()
            if existing:
                print(f"   📚 {student_data['name']} already exists. Skipping...")
                continue
            
            # Create student with secure token
            import hashlib, secrets
            secure_token = hashlib.sha256(f"{student_data['roll_number']}{student_data['name']}{secrets.token_hex(16)}".encode()).hexdigest()[:16]
            
            student = Student(
                name=student_data['name'],
                roll_number=student_data['roll_number'],
                parent_name=student_data['parent_name'],
                phone_number=student_data['phone_number'],
                secure_token=secure_token,
                photo_path=None,  # Photos to be added through web interface
                created_at=datetime.utcnow()
            )
            
            db.session.add(student)
            print(f"   ✅ Added: {student_data['name']} ({student_data['roll_number']})")
        
        # Generate today's daily code
        daily_code = generate_daily_code()
        
        db.session.commit()
        
        print("\n" + "=" * 50)
        print("🎉 Rural School Demo Data Created Successfully!")
        print("=" * 50)
        print(f"📅 Today's Daily Code: {daily_code}")
        print(f"👥 Students Created: {len(rural_students)}")
        print("\n🚀 Next Steps:")
        print("1. Run: python app_secure_rural.py")
        print("2. Open browser: http://localhost:5000")
        print("3. Choose attendance method:")
        print("   • Manual Digital (Teacher verifies visually)")
        print("   • Mobile Camera (Use smartphone)")
        print("   • Secure QR Codes (Daily changing codes)")
        print("\n📋 Available Attendance Methods:")
        print("✅ Manual Digital - Most secure, teacher sees each student")
        print("✅ Mobile Camera - Use teacher's phone for verification")
        print("✅ Secure QR - Daily codes that can't be shared")
        print("❌ RFID Removed - Too easy to cheat with shared cards")
        print("\n💡 Security Features:")
        print("• Daily changing verification codes")
        print("• Unique secure tokens per student")  
        print("• Visual verification required")
        print("• Time-stamped attendance records")
        print("• Cannot mark attendance remotely")

def show_daily_info():
    """Show today's attendance information"""
    with app.app_context():
        today = date.today()
        daily_code = generate_daily_code()
        
        students = Student.query.all()
        attendance_records = db.session.query(Attendance, Student).join(Student).filter(
            Attendance.date == today
        ).all()
        
        print(f"\n📊 Today's Attendance Summary ({today})")
        print("=" * 40)
        print(f"📅 Daily Code: {daily_code}")
        print(f"👥 Total Students: {len(students)}")
        print(f"✅ Present: {len(attendance_records)}")
        print(f"❌ Absent: {len(students) - len(attendance_records)}")
        
        if attendance_records:
            print(f"\n📝 Present Students:")
            for attendance, student in attendance_records:
                print(f"   • {student.name} ({student.roll_number}) - {attendance.time_in.strftime('%I:%M %p')} via {attendance.method}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'info':
        show_daily_info()
    else:
        create_rural_demo_data()
        
    print(f"\n💡 Tip: Run 'python {__file__} info' to see today's attendance summary")