from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import os
import cv2
import face_recognition
import numpy as np
import base64
from PIL import Image
import io
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance_group.db'
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
    photo_path = db.Column(db.String(200), nullable=False)
    face_encoding = db.Column(db.Text, nullable=True)  # Store face encoding as JSON
    parent_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with attendance records
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    method = db.Column(db.String(20), nullable=False, default='Group_Photo')
    status = db.Column(db.String(20), nullable=False, default='Present')
    confidence_score = db.Column(db.Float, nullable=True)  # Face recognition confidence
    
    # Ensure one attendance record per student per day
    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_attendance'),)

class GroupPhotoLog(db.Model):
    """Log of group photos taken for attendance"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time_taken = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    photo_path = db.Column(db.String(200), nullable=False)
    students_detected = db.Column(db.Integer, nullable=False, default=0)
    total_faces_found = db.Column(db.Integer, nullable=False, default=0)
    processing_time = db.Column(db.Float, nullable=True)  # Time taken to process

# Routes
@app.route('/')
def index():
    return render_template('index_group.html')

@app.route('/students')
def students():
    all_students = Student.query.all()
    return render_template('students_group.html', students=all_students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        parent_name = request.form.get('parent_name', '').strip()
        phone_number = request.form.get('phone_number', '').strip()
        
        # Check if roll number already exists
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            flash('Roll number already exists!', 'error')
            return render_template('add_student_group.html')
        
        # Handle file upload
        if 'photo' not in request.files:
            flash('No photo uploaded!', 'error')
            return render_template('add_student_group.html')
        
        file = request.files['photo']
        if file.filename == '':
            flash('No photo selected!', 'error')
            return render_template('add_student_group.html')
        
        if file:
            # Save the uploaded file
            filename = f"{roll_number}_{file.filename}"
            filepath = os.path.join('static/uploads', filename)
            file.save(filepath)
            
            # Generate face encoding
            try:
                image = face_recognition.load_image_file(filepath)
                face_encodings = face_recognition.face_encodings(image)
                
                if len(face_encodings) == 0:
                    flash('No face detected in the photo. Please upload a clear photo with a visible face.', 'error')
                    os.remove(filepath)
                    return render_template('add_student_group.html')
                
                # Use the first face encoding found
                face_encoding = face_encodings[0]
                face_encoding_json = json.dumps(face_encoding.tolist())
                
                # Create new student
                new_student = Student(
                    name=name,
                    roll_number=roll_number,
                    parent_name=parent_name,
                    phone_number=phone_number,
                    photo_path=filepath,
                    face_encoding=face_encoding_json
                )
                
                db.session.add(new_student)
                db.session.commit()
                
                flash('Student added successfully!', 'success')
                return redirect(url_for('students'))
                
            except Exception as e:
                flash(f'Error processing photo: {str(e)}', 'error')
                if os.path.exists(filepath):
                    os.remove(filepath)
                return render_template('add_student_group.html')
    
    return render_template('add_student_group.html')

@app.route('/attendance')
def attendance_page():
    return render_template('attendance_group.html')

@app.route('/group_attendance')
def group_attendance():
    """Group photo attendance page"""
    today = date.today()
    
    # Get today's attendance summary
    total_students = Student.query.count()
    present_today = Attendance.query.filter_by(date=today).count()
    
    # Get recent group photos
    recent_photos = GroupPhotoLog.query.filter_by(date=today).order_by(GroupPhotoLog.time_taken.desc()).limit(5).all()
    
    return render_template('group_attendance.html', 
                         total_students=total_students,
                         present_today=present_today,
                         recent_photos=recent_photos)

@app.route('/process_group_photo', methods=['POST'])
def process_group_photo():
    """Process group photo and identify all students"""
    try:
        start_time = datetime.utcnow()
        
        # Get image data from the request
        image_data = request.json['image']
        
        # Remove the data URL prefix
        image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save group photo for logging
        today = date.today()
        timestamp = datetime.utcnow().strftime('%H%M%S')
        group_photo_filename = f"group_{today}_{timestamp}.jpg"
        group_photo_path = os.path.join('static/uploads', group_photo_filename)
        image.save(group_photo_path)
        
        # Convert PIL image to numpy array for face_recognition
        image_array = np.array(image)
        
        # Find all face locations and encodings in the group photo
        face_locations = face_recognition.face_locations(image_array)
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if len(face_encodings) == 0:
            return jsonify({
                'success': False, 
                'message': 'No faces detected in the group photo. Please ensure good lighting and clear view of students.'
            })
        
        # Get all students from database
        all_students = Student.query.all()
        
        if not all_students:
            return jsonify({
                'success': False,
                'message': 'No students registered in the system. Please add students first.'
            })
        
        recognized_students = []
        unrecognized_faces = 0
        
        # Compare each face in the group photo with registered students
        for i, face_encoding in enumerate(face_encodings):
            best_match = None
            best_distance = float('inf')
            
            for student in all_students:
                if student.face_encoding:
                    # Load stored face encoding
                    stored_encoding = np.array(json.loads(student.face_encoding))
                    
                    # Calculate face distance (lower = better match)
                    distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
                    
                    if distance < best_distance and distance < 0.6:  # Confidence threshold
                        best_distance = distance
                        best_match = student
            
            if best_match:
                # Check if attendance already marked today
                existing_attendance = Attendance.query.filter_by(
                    student_id=best_match.id,
                    date=today
                ).first()
                
                if not existing_attendance:
                    # Mark attendance
                    new_attendance = Attendance(
                        student_id=best_match.id,
                        date=today,
                        time_in=datetime.utcnow(),
                        method='Group_Photo',
                        status='Present',
                        confidence_score=round((1 - best_distance) * 100, 2)  # Convert to percentage
                    )
                    db.session.add(new_attendance)
                    
                    recognized_students.append({
                        'name': best_match.name,
                        'roll_number': best_match.roll_number,
                        'confidence': round((1 - best_distance) * 100, 2),
                        'status': 'Attendance marked'
                    })
                else:
                    recognized_students.append({
                        'name': best_match.name,
                        'roll_number': best_match.roll_number,
                        'confidence': round((1 - best_distance) * 100, 2),
                        'status': 'Already marked today'
                    })
            else:
                unrecognized_faces += 1
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log the group photo
        group_log = GroupPhotoLog(
            date=today,
            time_taken=start_time,
            photo_path=group_photo_path,
            students_detected=len(recognized_students),
            total_faces_found=len(face_encodings),
            processing_time=processing_time
        )
        db.session.add(group_log)
        db.session.commit()
        
        # Prepare response
        response_data = {
            'success': True,
            'message': f'Group photo processed successfully!',
            'summary': {
                'total_faces_found': len(face_encodings),
                'students_recognized': len([s for s in recognized_students if s['status'] == 'Attendance marked']),
                'already_marked': len([s for s in recognized_students if s['status'] == 'Already marked today']),
                'unrecognized_faces': unrecognized_faces,
                'processing_time': round(processing_time, 2)
            },
            'recognized_students': recognized_students
        }
        
        if unrecognized_faces > 0:
            response_data['warnings'] = [
                f'{unrecognized_faces} face(s) could not be matched to registered students. They may need to be added to the system or the photo quality may need improvement.'
            ]
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error processing group photo: {str(e)}',
            'error_type': type(e).__name__
        })

@app.route('/manual_attendance_for_missed')
def manual_attendance_for_missed():
    """Manual attendance page for students who might have been missed in group photo"""
    today = date.today()
    
    # Get students who haven't been marked present today
    present_student_ids = db.session.query(Attendance.student_id).filter(
        Attendance.date == today
    ).subquery()
    
    absent_students = Student.query.filter(
        ~Student.id.in_(present_student_ids)
    ).all()
    
    return render_template('manual_missed_attendance.html', 
                         absent_students=absent_students,
                         today=today)

@app.route('/mark_missed_attendance', methods=['POST'])
def mark_missed_attendance():
    """Mark attendance for students who were missed in group photo"""
    try:
        student_ids = request.form.getlist('student_ids')
        today = date.today()
        
        marked_count = 0
        
        for student_id in student_ids:
            student = Student.query.get(int(student_id))
            if student:
                # Check if already marked (shouldn't happen, but safety check)
                existing = Attendance.query.filter_by(
                    student_id=student.id,
                    date=today
                ).first()
                
                if not existing:
                    attendance = Attendance(
                        student_id=student.id,
                        date=today,
                        time_in=datetime.utcnow(),
                        method='Manual_Missed',
                        status='Present',
                        confidence_score=100.0  # Manual verification = 100% confidence
                    )
                    db.session.add(attendance)
                    marked_count += 1
        
        db.session.commit()
        flash(f'Attendance marked for {marked_count} missed students!', 'success')
        
    except Exception as e:
        flash(f'Error marking attendance: {str(e)}', 'error')
    
    return redirect(url_for('manual_attendance_for_missed'))

@app.route('/reports')
def reports():
    # Get attendance data for today
    today = date.today()
    attendance_records = db.session.query(Attendance, Student).join(Student).filter(
        Attendance.date == today
    ).all()
    
    # Get group photo logs for today
    group_photos = GroupPhotoLog.query.filter_by(date=today).all()
    
    # Calculate statistics
    total_students = Student.query.count()
    present_count = len(attendance_records)
    absent_count = total_students - present_count
    
    return render_template('reports_group.html', 
                         attendance_records=attendance_records, 
                         group_photos=group_photos,
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
        
        group_photos = GroupPhotoLog.query.filter_by(date=report_date).all()
        
        total_students = Student.query.count()
        present_count = len(attendance_records)
        absent_count = total_students - present_count
        
        return render_template('reports_group.html', 
                             attendance_records=attendance_records,
                             group_photos=group_photos,
                             date=report_date,
                             total_students=total_students,
                             present_count=present_count,
                             absent_count=absent_count)
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('reports'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)