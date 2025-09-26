from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
import json
import hashlib
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance_secure.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create uploads directory if it doesn't exist
if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

db = SQLAlchemy(app)

# Database Models
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), nullable=False, unique=True)
    photo_path = db.Column(db.String(200), nullable=True)  # Optional photo
    phone_number = db.Column(db.String(15), nullable=True)  # For SMS notifications
    parent_name = db.Column(db.String(100), nullable=True)
    secure_token = db.Column(db.String(100), nullable=True)  # For secure QR codes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with attendance records
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    method = db.Column(db.String(20), nullable=False, default='Manual')  # Manual, Camera, QR_Mobile
    status = db.Column(db.String(20), nullable=False, default='Present')
    verification_code = db.Column(db.String(10), nullable=True)  # For manual verification
    
    # Ensure one attendance record per student per day
    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_attendance'),)

class DailyCode(db.Model):
    """Daily changing codes for secure attendance"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    daily_code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def generate_daily_code():
    """Generate a new daily code for attendance verification"""
    today = date.today()
    existing_code = DailyCode.query.filter_by(date=today).first()
    
    if existing_code:
        return existing_code.daily_code
    
    # Generate a new 6-digit code
    new_code = str(secrets.randbelow(900000) + 100000)
    
    daily_code_obj = DailyCode(date=today, daily_code=new_code)
    db.session.add(daily_code_obj)
    db.session.commit()
    
    return new_code

# Routes
@app.route('/')
def index():
    return render_template('index_secure.html')

@app.route('/students')
def students():
    all_students = Student.query.all()
    return render_template('students_secure.html', students=all_students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        phone_number = request.form.get('phone_number', '').strip()
        parent_name = request.form.get('parent_name', '').strip()
        
        # Check if roll number already exists
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            flash('Roll number already exists!', 'error')
            return render_template('add_student_secure.html')
        
        # Generate secure token for this student
        secure_token = hashlib.sha256(f"{roll_number}{name}{secrets.token_hex(16)}".encode()).hexdigest()[:16]
        
        # Handle optional photo upload
        photo_path = None
        if 'photo' in request.files and request.files['photo'].filename != '':
            file = request.files['photo']
            filename = f"{roll_number}_{file.filename}"
            filepath = os.path.join('static/uploads', filename)
            file.save(filepath)
            photo_path = filepath
        
        # Create new student
        new_student = Student(
            name=name,
            roll_number=roll_number,
            phone_number=phone_number if phone_number else None,
            parent_name=parent_name if parent_name else None,
            photo_path=photo_path,
            secure_token=secure_token,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_student)
        db.session.commit()
        
        flash('Student added successfully!', 'success')
        return redirect(url_for('students'))
    
    return render_template('add_student_secure.html')

@app.route('/attendance')
def attendance_page():
    # Get today's daily code object
    today = date.today()
    daily_code = DailyCode.query.filter_by(date=today).first()
    
    if not daily_code:
        # Generate daily code if it doesn't exist
        code_string = generate_daily_code()  # This creates the DailyCode object
        daily_code = DailyCode.query.filter_by(date=today).first()  # Get the created object
    
    return render_template('attendance_secure.html', daily_code=daily_code)

@app.route('/attendance/manual')
def manual_attendance():
    students = Student.query.all()
    today = date.today()
    
    # Get already marked attendance for today
    marked_students = db.session.query(Attendance.student_id).filter(
        Attendance.date == today
    ).all()
    marked_ids = [item[0] for item in marked_students]
    
    # Get today's daily code object
    daily_code = DailyCode.query.filter_by(date=today).first()
    if not daily_code:
        # Generate daily code if it doesn't exist
        code_string = generate_daily_code()  # This creates the DailyCode object
        daily_code = DailyCode.query.filter_by(date=today).first()  # Get the created object
    
    return render_template('manual_attendance_secure.html', 
                         students=students, 
                         marked_ids=marked_ids,
                         today=today,
                         daily_code=daily_code)

@app.route('/mark_manual_attendance', methods=['POST'])
def mark_manual_attendance():
    try:
        student_ids = request.form.getlist('student_ids')
        today = date.today()
        
        marked_count = 0
        
        for student_id in student_ids:
            student = Student.query.get(int(student_id))
            if student:
                # Check if already marked
                existing = Attendance.query.filter_by(
                    student_id=student.id,
                    date=today
                ).first()
                
                if not existing:
                    attendance = Attendance(
                        student_id=student.id,
                        date=today,
                        time_in=datetime.utcnow(),
                        method='Manual',
                        status='Present'
                    )
                    db.session.add(attendance)
                    marked_count += 1
        
        db.session.commit()
        flash(f'Attendance marked for {marked_count} students!', 'success')
        
    except Exception as e:
        flash(f'Error marking attendance: {str(e)}', 'error')
    
    return redirect(url_for('manual_attendance'))

@app.route('/attendance/mobile')
def mobile_attendance():
    """Mobile-based attendance for teachers with smartphones"""
    daily_code = generate_daily_code()
    students = Student.query.all()
    return render_template('mobile_attendance.html', students=students, daily_code=daily_code)

@app.route('/mark_mobile_attendance', methods=['POST'])
def mark_mobile_attendance():
    try:
        student_id = request.json.get('student_id')
        verification_code = request.json.get('verification_code', '').strip()
        
        if not student_id:
            return jsonify({'success': False, 'message': 'No student selected'})
        
        # Verify daily code
        today = date.today()
        daily_code_obj = DailyCode.query.filter_by(date=today).first()
        
        if not daily_code_obj or verification_code != daily_code_obj.daily_code:
            return jsonify({'success': False, 'message': 'Invalid verification code'})
        
        student = Student.query.get(int(student_id))
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Check if already marked today
        existing = Attendance.query.filter_by(
            student_id=student.id,
            date=today
        ).first()
        
        if existing:
            return jsonify({
                'success': False, 
                'message': f'{student.name} already marked attendance today'
            })
        
        # Mark attendance
        attendance = Attendance(
            student_id=student.id,
            date=today,
            time_in=datetime.utcnow(),
            method='Mobile',
            status='Present',
            verification_code=verification_code
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked for {student.name}',
            'student': {
                'name': student.name,
                'roll_number': student.roll_number,
                'time': datetime.utcnow().strftime('%I:%M %p')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/attendance/qr')
def qr_attendance():
    """QR code based attendance with daily verification"""
    daily_code = generate_daily_code()
    students = Student.query.all()
    return render_template('qr_attendance_secure.html', students=students, daily_code=daily_code)

@app.route('/generate_daily_qr/<int:student_id>')
def generate_daily_qr(student_id):
    """Generate a daily QR code for a student"""
    student = Student.query.get_or_404(student_id)
    daily_code = generate_daily_code()
    
    # Create secure QR data with daily code and student token
    qr_data = f"ATTEND:{date.today().isoformat()}:{student.secure_token}:{daily_code}:{student.roll_number}"
    
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for display
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'qr_image': f"data:image/png;base64,{img_str}",
            'student_name': student.name,
            'roll_number': student.roll_number,
            'valid_until': 'End of day',
            'security_note': 'QR code changes daily and is unique to each student'
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'QR code library not installed. Run: pip install qrcode[pil]'
        })

@app.route('/scan_qr_attendance', methods=['POST'])
def scan_qr_attendance():
    """Process scanned QR code for attendance"""
    try:
        qr_data = request.json.get('qr_data', '').strip()
        
        if not qr_data.startswith('ATTEND:'):
            return jsonify({'success': False, 'message': 'Invalid QR code format'})
        
        # Parse QR data: ATTEND:date:token:daily_code:roll_number
        parts = qr_data.split(':')
        if len(parts) != 5:
            return jsonify({'success': False, 'message': 'Invalid QR code structure'})
        
        qr_date, student_token, qr_daily_code, roll_number = parts[1], parts[2], parts[3], parts[4]
        
        # Verify date (must be today)
        if qr_date != date.today().isoformat():
            return jsonify({'success': False, 'message': 'QR code expired (not for today)'})
        
        # Verify daily code
        today = date.today()
        daily_code_obj = DailyCode.query.filter_by(date=today).first()
        if not daily_code_obj or qr_daily_code != daily_code_obj.daily_code:
            return jsonify({'success': False, 'message': 'Invalid or expired daily code'})
        
        # Find student by token and roll number
        student = Student.query.filter_by(
            secure_token=student_token,
            roll_number=roll_number
        ).first()
        
        if not student:
            return jsonify({'success': False, 'message': 'Student not found or invalid token'})
        
        # Check if already marked today
        existing = Attendance.query.filter_by(
            student_id=student.id,
            date=today
        ).first()
        
        if existing:
            return jsonify({
                'success': False, 
                'message': f'{student.name} already marked attendance today'
            })
        
        # Mark attendance
        attendance = Attendance(
            student_id=student.id,
            date=today,
            time_in=datetime.utcnow(),
            method='QR_Secure',
            status='Present',
            verification_code=qr_daily_code
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Attendance marked for {student.name}',
            'student': {
                'name': student.name,
                'roll_number': student.roll_number,
                'time': datetime.utcnow().strftime('%I:%M %p')
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing QR code: {str(e)}'})

@app.route('/reports')
def reports():
    # Get attendance data for today
    today = date.today()
    attendance_records = db.session.query(Attendance, Student).join(Student).filter(
        Attendance.date == today
    ).all()
    
    # Get total students count
    total_students = Student.query.count()
    present_count = len(attendance_records)
    absent_count = total_students - present_count
    
    return render_template('reports_secure.html', 
                         attendance_records=attendance_records, 
                         date=today,
                         total_students=total_students,
                         present_count=present_count,
                         absent_count=absent_count)

@app.route('/reports/<date_str>')
def reports_by_date(date_str):
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        attendance_records = db.session.query(Attendance, Student).join(Student).filter(
            Attendance.date == report_date
        ).all()
        
        total_students = Student.query.count()
        present_count = len(attendance_records)
        absent_count = total_students - present_count
        
        return render_template('reports_secure.html', 
                             attendance_records=attendance_records, 
                             date=report_date,
                             total_students=total_students,
                             present_count=present_count,
                             absent_count=absent_count)
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('reports'))

@app.route('/get_daily_code')
def get_daily_code():
    """API endpoint to get today's daily code for teachers"""
    daily_code = generate_daily_code()
    return jsonify({'daily_code': daily_code, 'date': date.today().isoformat()})

@app.route('/delete_student', methods=['POST'])
def delete_student():
    """Delete individual student and their data"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'success': False, 'message': 'Student ID is required'})
        
        # Find the student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        student_name = student.name
        photo_path = student.photo_path
        
        # Delete attendance records first (foreign key constraint)
        Attendance.query.filter_by(student_id=student_id).delete()
        
        # Delete the student
        db.session.delete(student)
        db.session.commit()
        
        # Clean up photo file
        if photo_path:
            full_path = os.path.join("static", photo_path.lstrip('/'))
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except Exception as e:
                    print(f"Error removing photo file: {e}")
        
        return jsonify({
            'success': True, 
            'message': f'Student {student_name} deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting student: {str(e)}'})

@app.route('/delete_all_students', methods=['POST'])
def delete_all_students():
    """Delete all students and their data"""
    try:
        # Count before deletion
        student_count = Student.query.count()
        attendance_count = Attendance.query.count()
        
        if student_count == 0:
            return jsonify({'success': True, 'message': 'No students to delete'})
        
        # Get all photo paths before deletion
        students = Student.query.all()
        photo_paths = [student.photo_path for student in students if student.photo_path]
        
        # Delete all attendance records first
        Attendance.query.delete()
        
        # Delete all students
        Student.query.delete()
        
        db.session.commit()
        
        # Clean up photo files
        removed_photos = 0
        for photo_path in photo_paths:
            full_path = os.path.join("static", photo_path.lstrip('/'))
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    removed_photos += 1
                except Exception as e:
                    print(f"Error removing photo file {photo_path}: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {student_count} students, {attendance_count} attendance records, and {removed_photos} photos'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting students: {str(e)}'})

@app.route('/export_students')
def export_students():
    """Export student data as CSV"""
    try:
        import csv
        from io import StringIO
        from flask import make_response
        
        students = Student.query.all()
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Name', 'Roll Number', 'Parent Name', 'Phone Number', 'Registration Date', 'Has Photo', 'Has Secure Token'])
        
        # Write student data
        for student in students:
            writer.writerow([
                student.id,
                student.name,
                student.roll_number,
                student.parent_name or '',
                student.phone_number or '',
                student.created_at.strftime('%Y-%m-%d'),
                'Yes' if student.photo_path else 'No',
                'Yes' if student.secure_token else 'No'
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=students_export_{date.today().isoformat()}.csv'
        
        return response
        
    except Exception as e:
        flash(f'Error exporting students: {str(e)}', 'error')
        return redirect(url_for('students'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)