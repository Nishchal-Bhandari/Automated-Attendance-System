from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance_rfid.db'
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
    rfid_tag = db.Column(db.String(50), nullable=True, unique=True)  # RFID tag ID
    photo_path = db.Column(db.String(200), nullable=True)  # Optional photo
    phone_number = db.Column(db.String(15), nullable=True)  # For SMS notifications
    parent_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with attendance records
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    method = db.Column(db.String(20), nullable=False, default='Manual')  # Manual, RFID, QR, Mobile
    status = db.Column(db.String(20), nullable=False, default='Present')
    
    # Ensure one attendance record per student per day
    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_attendance'),)

# Routes
@app.route('/')
def index():
    return render_template('index_rural.html')

@app.route('/students')
def students():
    all_students = Student.query.all()
    return render_template('students_rural.html', students=all_students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        rfid_tag = request.form.get('rfid_tag', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        parent_name = request.form.get('parent_name', '').strip()
        
        # Check if roll number already exists
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            flash('Roll number already exists!', 'error')
            return render_template('add_student_rural.html')
        
        # Check if RFID tag already exists (if provided)
        if rfid_tag:
            existing_rfid = Student.query.filter_by(rfid_tag=rfid_tag).first()
            if existing_rfid:
                flash('RFID tag already assigned to another student!', 'error')
                return render_template('add_student_rural.html')
        
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
            rfid_tag=rfid_tag if rfid_tag else None,
            phone_number=phone_number if phone_number else None,
            parent_name=parent_name if parent_name else None,
            photo_path=photo_path,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_student)
        db.session.commit()
        
        flash('Student added successfully!', 'success')
        return redirect(url_for('students'))
    
    return render_template('add_student_rural.html')

@app.route('/attendance')
def attendance_page():
    return render_template('attendance_rural.html')

@app.route('/attendance/manual')
def manual_attendance():
    students = Student.query.all()
    today = date.today()
    
    # Get already marked attendance for today
    marked_students = db.session.query(Attendance.student_id).filter(
        Attendance.date == today
    ).all()
    marked_ids = [item[0] for item in marked_students]
    
    return render_template('manual_attendance.html', 
                         students=students, 
                         marked_ids=marked_ids,
                         today=today)

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

@app.route('/attendance/rfid')
def rfid_attendance():
    return render_template('rfid_attendance.html')

@app.route('/mark_rfid_attendance', methods=['POST'])
def mark_rfid_attendance():
    try:
        rfid_tag = request.json.get('rfid_tag', '').strip()
        
        if not rfid_tag:
            return jsonify({'success': False, 'message': 'No RFID tag provided'})
        
        # Find student with this RFID tag
        student = Student.query.filter_by(rfid_tag=rfid_tag).first()
        
        if not student:
            return jsonify({'success': False, 'message': 'RFID tag not registered'})
        
        today = date.today()
        
        # Check if already marked today
        existing = Attendance.query.filter_by(
            student_id=student.id,
            date=today
        ).first()
        
        if existing:
            return jsonify({
                'success': False, 
                'message': f'{student.name} already marked attendance today',
                'student': {
                    'name': student.name,
                    'roll_number': student.roll_number
                }
            })
        
        # Mark attendance
        attendance = Attendance(
            student_id=student.id,
            date=today,
            time_in=datetime.utcnow(),
            method='RFID',
            status='Present'
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
    
    return render_template('reports_rural.html', 
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
        
        return render_template('reports_rural.html', 
                             attendance_records=attendance_records, 
                             date=report_date,
                             total_students=total_students,
                             present_count=present_count,
                             absent_count=absent_count)
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('reports'))

@app.route('/qr_attendance')
def qr_attendance():
    students = Student.query.all()
    return render_template('qr_attendance.html', students=students)

@app.route('/generate_qr/<int:student_id>')
def generate_qr(student_id):
    student = Student.query.get_or_404(student_id)
    
    # Generate QR code data (simple format)
    qr_data = f"STUDENT:{student.roll_number}:{student.name}"
    
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
            'roll_number': student.roll_number
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'message': 'QR code library not installed. Run: pip install qrcode[pil]'
        })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)