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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with attendance records
    attendance_records = db.relationship('Attendance', backref='student', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Present')
    
    # Ensure one attendance record per student per day
    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_attendance'),)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/students')
def students():
    all_students = Student.query.all()
    return render_template('students.html', students=all_students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        
        # Check if roll number already exists
        existing_student = Student.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            flash('Roll number already exists!', 'error')
            return render_template('add_student.html')
        
        # Handle file upload
        if 'photo' not in request.files:
            flash('No photo uploaded!', 'error')
            return render_template('add_student.html')
        
        file = request.files['photo']
        if file.filename == '':
            flash('No photo selected!', 'error')
            return render_template('add_student.html')
        
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
                    os.remove(filepath)  # Remove the uploaded file
                    return render_template('add_student.html')
                
                # Use the first face encoding found
                face_encoding = face_encodings[0]
                face_encoding_json = json.dumps(face_encoding.tolist())
                
                # Create new student
                new_student = Student(
                    name=name,
                    roll_number=roll_number,
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
                return render_template('add_student.html')
    
    return render_template('add_student.html')

@app.route('/attendance')
def attendance_page():
    return render_template('attendance.html')

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        # Get image data from the request
        image_data = request.json['image']
        
        # Remove the data URL prefix
        image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert PIL image to numpy array for face_recognition
        image_array = np.array(image)
        
        # Find face encodings in the captured image
        face_encodings = face_recognition.face_encodings(image_array)
        
        if len(face_encodings) == 0:
            return jsonify({'success': False, 'message': 'No face detected in the image'})
        
        # Get all students from database
        all_students = Student.query.all()
        
        recognized_students = []
        
        for face_encoding in face_encodings:
            for student in all_students:
                if student.face_encoding:
                    # Load stored face encoding
                    stored_encoding = np.array(json.loads(student.face_encoding))
                    
                    # Compare faces
                    matches = face_recognition.compare_faces([stored_encoding], face_encoding, tolerance=0.6)
                    
                    if matches[0]:
                        # Check if attendance already marked today
                        today = date.today()
                        existing_attendance = Attendance.query.filter_by(
                            student_id=student.id,
                            date=today
                        ).first()
                        
                        if not existing_attendance:
                            # Mark attendance
                            new_attendance = Attendance(
                                student_id=student.id,
                                date=today,
                                time_in=datetime.utcnow(),
                                status='Present'
                            )
                            db.session.add(new_attendance)
                            db.session.commit()
                            
                            recognized_students.append({
                                'name': student.name,
                                'roll_number': student.roll_number,
                                'status': 'Attendance marked'
                            })
                        else:
                            recognized_students.append({
                                'name': student.name,
                                'roll_number': student.roll_number,
                                'status': 'Already marked today'
                            })
                        break
        
        if recognized_students:
            return jsonify({
                'success': True,
                'message': 'Students recognized',
                'students': recognized_students
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No registered students recognized in the image'
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
    
    return render_template('reports.html', attendance_records=attendance_records, date=today)

@app.route('/reports/<date_str>')
def reports_by_date(date_str):
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        attendance_records = db.session.query(Attendance, Student).join(Student).filter(
            Attendance.date == report_date
        ).all()
        
        return render_template('reports.html', attendance_records=attendance_records, date=report_date)
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('reports'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)