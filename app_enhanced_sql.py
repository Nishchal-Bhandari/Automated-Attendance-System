"""
Enhanced Flask Application with SQL Database Integration
Supports multiple SQL databases and photo BLOB storage
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import json
import secrets
import hashlib
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2

# Import our enhanced configuration and models
from database_config import get_config, test_database_connection, init_database
from models_enhanced import db, Student, Attendance, DailyCode, PhotoMetadata, AttendanceSession

# Face recognition import (existing)
try:
    from mediapipe_face_recognition import MediaPipeFaceRecognition
    FACE_RECOGNITION_AVAILABLE = True
    print("✅ MediaPipe Face Recognition loaded successfully!")
except ImportError as e:
    FACE_RECOGNITION_AVAILABLE = False
    print(f"⚠️  Face recognition not available: {e}")

# Initialize Flask app with enhanced configuration
def create_app(config_class=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    
    # Initialize database
    db.init_app(app)
    
    # Create uploads directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Test database connection
    with app.app_context():
        if test_database_connection(app):
            init_database(app, db)
        else:
            print("❌ Database connection failed. Please check configuration.")
    
    return app

# Create app instance
app = create_app()

# Initialize face recognition
face_recognizer = None
if FACE_RECOGNITION_AVAILABLE:
    try:
        face_recognizer = MediaPipeFaceRecognition()
    except Exception as e:
        print(f"⚠️  Face recognition initialization failed: {e}")
        FACE_RECOGNITION_AVAILABLE = False

# Utility functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_photo_to_db(student, photo_file):
    """Save photo to database as BLOB and create metadata"""
    try:
        # Read photo data
        photo_data = photo_file.read()
        photo_file.seek(0)  # Reset file pointer
        
        # Open image to get metadata
        image = Image.open(photo_file)
        width, height = image.size
        format_type = image.format
        
        # Save photo in student record
        student.set_photo_blob(photo_data)
        
        # Create photo metadata
        metadata = PhotoMetadata(
            student_id=student.id,
            filename=photo_file.filename,
            original_filename=photo_file.filename,
            file_size=len(photo_data),
            mime_type=photo_file.content_type or 'image/jpeg',
            width=width,
            height=height,
            format=format_type,
            uploaded_by='System',
            upload_method='web'
        )
        
        db.session.add(metadata)
        
        # Also save to disk as backup if configured
        if app.config.get('STORE_PHOTOS_ON_DISK', True):
            filename = f"{student.roll_number}_{hashlib.md5(photo_data).hexdigest()[:8]}.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save to disk
            with open(filepath, 'wb') as f:
                f.write(photo_data)
            
            student.photo_path = f"uploads/{filename}"
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving photo: {e}")
        return False

def generate_daily_code():
    """Generate or get today's daily code"""
    today = date.today()
    existing_code = DailyCode.query.filter_by(date=today).first()
    
    if existing_code and existing_code.is_valid():
        return existing_code.daily_code
    
    # Generate new code
    new_code = str(secrets.randbelow(900000) + 100000)
    
    daily_code_obj = DailyCode(
        date=today,
        daily_code=new_code,
        created_by='System',
        max_usage=1000
    )
    daily_code_obj.generate_code_hash()
    
    db.session.add(daily_code_obj)
    db.session.commit()
    
    return new_code

# Routes
@app.route('/')
def index():
    """Enhanced home page with database statistics"""
    from models_enhanced import get_database_stats
    stats = get_database_stats()
    return render_template('index_enhanced.html', stats=stats)

@app.route('/students')
def students():
    """Enhanced students page with photo display from database"""
    students = Student.query.all()
    return render_template('students_enhanced.html', students=students)

@app.route('/student/<int:student_id>')
def view_student(student_id):
    """View individual student details"""
    student = Student.query.get_or_404(student_id)
    return render_template('view_student.html', student=student)

@app.route('/student_photo/<int:student_id>')
def student_photo(student_id):
    """Serve student photo from database BLOB"""
    student = Student.query.get_or_404(student_id)
    
    if not student.photo_blob:
        return redirect(url_for('static', filename='images/default_avatar.png'))
    
    return send_file(
        BytesIO(student.photo_blob),
        mimetype='image/jpeg',
        as_attachment=False
    )

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    """Enhanced student registration with photo BLOB storage"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            roll_number = request.form.get('roll_number', '').strip()
            class_name = request.form.get('class_name', '').strip()
            section = request.form.get('section', '').strip()
            parent_name = request.form.get('parent_name', '').strip()
            phone_number = request.form.get('phone_number', '').strip()
            parent_phone = request.form.get('parent_phone', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validation
            if not name or not roll_number:
                flash('Name and Roll Number are required!', 'error')
                return render_template('add_student_enhanced.html')
            
            # Check if student already exists
            existing_student = Student.query.filter_by(roll_number=roll_number).first()
            if existing_student:
                flash('Student with this roll number already exists!', 'error')
                return render_template('add_student_enhanced.html')
            
            # Create new student
            student = Student(
                name=name,
                roll_number=roll_number,
                class_name=class_name,
                section=section,
                parent_name=parent_name,
                phone_number=phone_number,
                parent_phone=parent_phone,
                address=address
            )
            
            # Generate secure token
            student.generate_secure_token()
            
            # Handle photo upload
            photo_file = request.files.get('photo')
            if photo_file and photo_file.filename and allowed_file(photo_file.filename):
                # Save to database
                db.session.add(student)
                db.session.flush()  # Get the student ID
                
                if save_photo_to_db(student, photo_file):
                    # Generate face encoding if face recognition is available
                    if FACE_RECOGNITION_AVAILABLE and face_recognizer:
                        try:
                            # Convert BLOB to image array
                            image_array = np.frombuffer(student.photo_blob, np.uint8)
                            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                            
                            # Detect faces and create encoding
                            faces = face_recognizer.detect_faces(image)
                            if faces:
                                encoding = face_recognizer.generate_face_encoding(faces[0]['face_region'])
                                if encoding is not None:
                                    student.face_encoding = encoding.astype(np.float32).tobytes()
                                    student.face_confidence = 0.8  # Initial confidence
                                    
                                    # Update metadata
                                    metadata = student.photo_metadata[0]
                                    metadata.face_detected = True
                                    metadata.is_processed = True
                                    metadata.processing_notes = "Face encoding created successfully"
                                else:
                                    flash('Photo uploaded but face encoding failed. Face recognition may not work optimally.', 'warning')
                            else:
                                flash('No face detected in photo. Please upload a clear face photo for better recognition.', 'warning')
                        
                        except Exception as e:
                            flash(f'Photo uploaded but face processing failed: {str(e)}', 'warning')
                else:
                    flash('Failed to save photo. Student created without photo.', 'warning')
            
            db.session.commit()
            flash(f'Student {name} added successfully!', 'success')
            return redirect(url_for('students'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {str(e)}', 'error')
    
    return render_template('add_student_enhanced.html')

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit student details"""
    student = Student.query.get_or_404(student_id)
    
    if not student.is_active:
        flash('Student not found!', 'error')
        return redirect(url_for('students'))
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            roll_number = request.form.get('roll_number', '').strip()
            class_name = request.form.get('class_name', '').strip()
            section = request.form.get('section', '').strip()
            parent_name = request.form.get('parent_name', '').strip()
            phone_number = request.form.get('phone_number', '').strip()
            parent_phone = request.form.get('parent_phone', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validation
            if not name or not roll_number:
                flash('Name and Roll Number are required!', 'error')
                return render_template('edit_student.html', student=student)
            
            # Check if roll number is already taken by another student
            existing_student = Student.query.filter_by(roll_number=roll_number).filter(Student.id != student_id).first()
            if existing_student:
                flash('Roll number already exists for another student!', 'error')
                return render_template('edit_student.html', student=student)
            
            # Update student details
            student.name = name
            student.roll_number = roll_number
            student.class_name = class_name
            student.section = section
            student.parent_name = parent_name
            student.phone_number = phone_number
            student.parent_phone = parent_phone
            student.address = address
            
            # Handle photo upload if provided
            photo = request.files.get('photo')
            if photo and photo.filename:
                try:
                    # Process and save photo
                    photo_blob = photo.read()
                    
                    if len(photo_blob) > 5 * 1024 * 1024:  # 5MB limit
                        flash('Photo file too large. Please choose a smaller image.', 'error')
                        return render_template('edit_student.html', student=student)
                    
                    student.photo_blob = photo_blob
                    student.photo_filename = secure_filename(photo.filename)
                    
                    # Update face encoding if face recognition is available
                    if FACE_RECOGNITION_AVAILABLE and face_recognizer:
                        try:
                            # Convert blob to image for face processing
                            image = cv2.imdecode(np.frombuffer(photo_blob, np.uint8), cv2.IMREAD_COLOR)
                            
                            if image is not None:
                                # Detect faces and generate encoding
                                faces = face_recognizer.detect_faces(image)
                                if faces:
                                    face_encoding = face_recognizer.generate_face_encoding(faces[0]['face_region'])
                                    if face_encoding is not None:
                                        student.face_encoding = face_encoding.astype(np.float32).tobytes()
                                        flash('Photo and face encoding updated successfully!', 'success')
                                    else:
                                        flash('Photo updated but face encoding failed. Face recognition may not work optimally.', 'warning')
                                else:
                                    flash('Photo updated but no face detected. Face recognition may not work optimally.', 'warning')
                            else:
                                flash('Photo updated but face processing failed.', 'warning')
                        except Exception as e:
                            flash(f'Photo updated but face processing failed: {str(e)}', 'warning')
                    
                except Exception as e:
                    flash(f'Error uploading photo: {str(e)}', 'error')
                    return render_template('edit_student.html', student=student)
            
            db.session.commit()
            flash(f'Student {name} updated successfully!', 'success')
            return redirect(url_for('view_student', student_id=student.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {str(e)}', 'error')
    
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Permanently delete student from database"""
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.name  # Store name before deletion
        
        # Delete the student (this will cascade delete attendance records and photo metadata)
        db.session.delete(student)
        db.session.commit()
        
        flash(f'Student {student_name} has been permanently deleted from the database!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('students'))

@app.route('/attendance')
def attendance_page():
    """Enhanced attendance page"""
    # Get today's daily code
    today = date.today()
    daily_code = DailyCode.query.filter_by(date=today).first()
    
    if not daily_code:
        code_string = generate_daily_code()
        daily_code = DailyCode.query.filter_by(date=today).first()
    
    # Get attendance statistics for today
    total_students = Student.query.filter_by(is_active=True).count()
    present_today = Attendance.query.filter_by(date=today).count()
    
    stats = {
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': total_students - present_today,
        'attendance_percentage': (present_today / total_students * 100) if total_students > 0 else 0
    }
    
    return render_template('attendance_enhanced.html', daily_code=daily_code, stats=stats)

@app.route('/detect_faces_live', methods=['POST'])
def detect_faces_live():
    """Enhanced live face detection with database lookup"""
    if not FACE_RECOGNITION_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'Face recognition is not available on this system'
        })
    
    try:
        # Handle both form data and JSON data
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle form data (file upload)
            photo = request.files.get('image') or request.files.get('photo')
            if not photo:
                return jsonify({'success': False, 'message': 'No image file received'})
            image_bytes = photo.read()
            image_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        else:
            # Handle JSON data (base64 encoded)
            image_data = request.json.get('image')
            if not image_data:
                return jsonify({'success': False, 'message': 'No image data received'})
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            image_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        # Detect faces
        faces = face_recognizer.detect_faces(image)
        
        if not faces:
            return jsonify({
                'success': True,
                'faces': [],
                'count': 0
            })
        
        # Load all student encodings from database
        students_with_encodings = Student.query.filter(
            Student.face_encoding.isnot(None),
            Student.is_active == True
        ).all()
        
        known_faces = []
        
        for student in students_with_encodings:
            try:
                encoding = np.frombuffer(student.face_encoding, dtype=np.float32)
                known_faces.append({
                    'id': student.id,
                    'name': student.name,
                    'roll_number': student.roll_number,
                    'encoding': encoding
                })
            except Exception as e:
                print(f"Error loading encoding for {student.name}: {e}")
        
        # Identify faces using the correct method
        if known_faces:
            results = face_recognizer.identify_faces(image, known_faces)
            
            # Mark attendance for recognized faces
            today = date.today()
            marked_students = []
            
            for result in results:
                if result.get('identified') and result.get('student_info') and result.get('similarity', 0) > 0.6:
                    # Get student info from result
                    student_info = result['student_info']
                    student_id = student_info['id']
                    student_name = student_info['name']
                    
                    # Check if already marked today
                    existing_attendance = Attendance.query.filter_by(
                        student_id=student_id,
                        date=today
                    ).first()
                    
                    if not existing_attendance:
                        # Mark attendance
                        attendance = Attendance(
                            student_id=student_id,
                            date=today,
                            time_in=datetime.utcnow(),
                            status='Present',
                            method='Camera',
                            confidence=result.get('similarity', 0)
                        )
                        db.session.add(attendance)
                        marked_students.append(student_name)
            
            if marked_students:
                db.session.commit()
            
            # Format results for frontend
            face_data = []
            for i, result in enumerate(results):
                # Get name from student_info or default to 'Unknown'
                name = 'Unknown'
                if result.get('identified') and result.get('student_info'):
                    name = result['student_info']['name']
                
                face_data.append({
                    'name': name,
                    'confidence': result.get('similarity', 0.0),
                    'bbox': faces[i] if i < len(faces) else None,
                    'status': 'marked' if name in marked_students else 'recognized'
                })
            
            return jsonify({
                'success': True,
                'faces': face_data,
                'count': len(face_data),
                'marked_students': marked_students
            })
        
        else:
            return jsonify({
                'success': True,
                'faces': [],
                'count': len(faces),
                'message': 'Faces detected but no student encodings available for recognition'
            })
    
    except Exception as e:
        print(f"❌ Error in detect_faces_live: {e}")
        return jsonify({
            'success': False,
            'message': f'Error detecting faces: {str(e)}'
        })

@app.route('/reports')
def reports():
    """Reports page showing attendance statistics and records"""
    from datetime import datetime, date, timedelta
    
    # Get filter parameters
    selected_date = request.args.get('date')
    student_filter = request.args.get('student_id')
    status_filter = request.args.get('status')
    
    # Base query
    query = Attendance.query.join(Student)
    
    # Apply filters
    if selected_date:
        try:
            filter_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            query = query.filter(Attendance.date == filter_date)
        except ValueError:
            selected_date = None
    
    if student_filter:
        try:
            student_id = int(student_filter)
            query = query.filter(Attendance.student_id == student_id)
        except ValueError:
            student_filter = None
    
    if status_filter:
        query = query.filter(Attendance.status == status_filter)
    
    # Get attendance records
    attendance_records = query.order_by(Attendance.date.desc(), Attendance.created_at.desc()).all()
    
    # Get all students for filter dropdown
    all_students = Student.query.filter(Student.is_active == True).order_by(Student.name).all()
    
    # Calculate statistics
    total_records = len(attendance_records)
    present_count = sum(1 for record in attendance_records if record.status == 'Present')
    absent_count = sum(1 for record in attendance_records if record.status == 'Absent')
    
    # Get today's attendance summary
    today = date.today()
    today_attendance = Attendance.query.filter(Attendance.date == today).all()
    today_present = sum(1 for record in today_attendance if record.status == 'Present')
    today_total = len(today_attendance)
    
    # Get weekly summary
    week_start = today - timedelta(days=today.weekday())
    weekly_attendance = Attendance.query.filter(
        Attendance.date >= week_start,
        Attendance.date <= today
    ).all()
    
    weekly_stats = {}
    for record in weekly_attendance:
        day_name = record.date.strftime('%A')
        if day_name not in weekly_stats:
            weekly_stats[day_name] = {'present': 0, 'total': 0}
        weekly_stats[day_name]['total'] += 1
        if record.status == 'Present':
            weekly_stats[day_name]['present'] += 1
    
    stats = {
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count,
        'today_present': today_present,
        'today_total': today_total,
        'weekly_stats': weekly_stats
    }
    
    return render_template('reports.html', 
                         attendance_records=attendance_records,
                         all_students=all_students,
                         stats=stats,
                         selected_date=selected_date,
                         student_filter=student_filter,
                         status_filter=status_filter)

@app.route('/database_stats')
def database_stats():
    """API endpoint for database statistics"""
    from models_enhanced import get_database_stats
    stats = get_database_stats()
    return jsonify(stats)

@app.route('/admin/database')
def admin_database():
    """Admin page for database management"""
    from models_enhanced import get_database_stats
    stats = get_database_stats()
    
    # Get recent activity
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    recent_attendance = Attendance.query.order_by(Attendance.created_at.desc()).limit(5).all()
    
    return render_template('admin_database.html', 
                         stats=stats,
                         recent_students=recent_students,
                         recent_attendance=recent_attendance)

@app.route('/api/students')
def api_students():
    """API endpoint to get all active students"""
    students = Student.query.filter(Student.is_active == True).order_by(Student.name).all()
    return jsonify([{
        'id': student.id,
        'name': student.name,
        'roll_number': student.roll_number,
        'class_name': student.class_name
    } for student in students])

@app.route('/api/recent_attendance')
def api_recent_attendance():
    """API endpoint to get recent attendance records"""
    from datetime import datetime, date
    
    # Get today's attendance records
    today = date.today()
    records = db.session.query(Attendance, Student).join(Student).filter(
        Attendance.date == today
    ).order_by(Attendance.created_at.desc()).limit(10).all()
    
    return jsonify([{
        'student_name': record.Student.name,
        'roll_number': record.Student.roll_number,
        'status': record.Attendance.status,
        'created_at': record.Attendance.created_at.isoformat() if record.Attendance.created_at else None
    } for record in records])

@app.route('/mark_attendance_auto', methods=['POST'])
def mark_attendance_auto():
    """API endpoint to automatically mark attendance for detected students"""
    data = request.get_json()
    student_id = data.get('student_id')
    code = data.get('code')
    
    if not student_id or not code:
        return jsonify({'success': False, 'message': 'Student ID and code required'})
    
    # Verify daily code
    daily_code = DailyCode.query.filter_by(
        date=date.today(),
        code=code,
        is_active=True
    ).first()
    
    if not daily_code:
        return jsonify({'success': False, 'message': 'Invalid attendance code'})
    
    # Check if already marked today
    existing_attendance = Attendance.query.filter_by(
        student_id=student_id,
        date=date.today()
    ).first()
    
    if existing_attendance:
        return jsonify({'success': False, 'message': 'Attendance already marked for today'})
    
    # Get student
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'})
    
    # Mark attendance
    attendance = Attendance(
        student_id=student_id,
        date=date.today(),
        status='Present',
        method='Face Recognition',
        device_info=request.headers.get('User-Agent', 'Unknown'),
        created_at=datetime.now()
    )
    
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'Attendance marked for {student.name}',
        'student_name': student.name
    })

@app.route('/manual_attendance', methods=['POST'])
def manual_attendance():
    """Handle manual attendance marking"""
    student_id = request.form.get('student_id')
    code = request.form.get('code')
    
    if not student_id or not code:
        flash('Student and code are required', 'error')
        return redirect(url_for('attendance_page'))
    
    # Verify daily code
    daily_code = DailyCode.query.filter_by(
        date=date.today(),
        code=code,
        is_active=True
    ).first()
    
    if not daily_code:
        flash('Invalid attendance code', 'error')
        return redirect(url_for('attendance_page'))
    
    # Check if already marked today
    existing_attendance = Attendance.query.filter_by(
        student_id=student_id,
        date=date.today()
    ).first()
    
    if existing_attendance:
        flash('Attendance already marked for this student today', 'warning')
        return redirect(url_for('attendance_page'))
    
    # Get student
    student = Student.query.get(student_id)
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('attendance_page'))
    
    # Mark attendance
    attendance = Attendance(
        student_id=student_id,
        date=date.today(),
        status='Present',
        method='Manual Entry',
        device_info=request.headers.get('User-Agent', 'Unknown'),
        created_at=datetime.now()
    )
    
    db.session.add(attendance)
    db.session.commit()
    
    flash(f'Attendance marked successfully for {student.name}', 'success')
    return redirect(url_for('attendance_page'))

@app.route('/api/students_with_encodings')
def api_students_with_encodings():
    """API endpoint to get all active students with face encodings"""
    students = Student.query.filter(Student.is_active == True).order_by(Student.name).all()
    
    students_data = []
    for student in students:
        student_data = {
            'id': student.id,
            'name': student.name,
            'roll_number': student.roll_number,
            'class_name': student.class_name,
            'has_photo': student.photo_blob is not None
        }
        
        # Generate face encoding if not exists and photo is available
        if student.photo_blob and not student.face_encoding:
            try:
                # Generate face encoding from photo
                if FACE_RECOGNITION_AVAILABLE:
                    face_rec = MediaPipeFaceRecognition()
                    
                    # Convert BLOB to image
                    from PIL import Image
                    import io
                    image = Image.open(io.BytesIO(student.photo_blob))
                    image_array = np.array(image)
                    
                    # Generate encoding
                    faces = face_rec.detect_faces(image_array)
                    if faces:
                        encoding = face_rec.generate_face_encoding(faces[0]['face_region'])
                        if encoding is not None:
                            # Store encoding in database
                            student.face_encoding = encoding.tobytes()
                            db.session.commit()
                            student_data['encoding'] = encoding.tolist()
            except Exception as e:
                print(f"Error generating encoding for {student.name}: {e}")
        
        elif student.face_encoding:
            # Load existing encoding
            try:
                encoding_array = np.frombuffer(student.face_encoding, dtype=np.float32)
                student_data['encoding'] = encoding_array.tolist()
            except Exception as e:
                print(f"Error loading encoding for {student.name}: {e}")
        
        students_data.append(student_data)
    
    return jsonify(students_data)

@app.route('/detect_and_identify_faces', methods=['POST'])
def detect_and_identify_faces():
    """Enhanced face detection and identification endpoint"""
    if not FACE_RECOGNITION_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'Face recognition not available'
        })
    
    try:
        print("📸 Face detection request received")
        # Handle both 'image' and 'photo' field names
        photo = request.files.get('image') or request.files.get('photo')
        if not photo:
            print("❌ No photo file received")
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            })
        
        # Read image data
        image_data = photo.read()
        
        # Initialize face recognition
        face_rec = MediaPipeFaceRecognition()
        
        # Convert to numpy array
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({
                'success': False,
                'error': 'Invalid image format'
            })
        
        # Get all students with encodings - use raw SQL to bypass SQLAlchemy issues
        import sqlite3
        try:
            conn = sqlite3.connect('attendance_enhanced.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, roll_number, face_encoding FROM student WHERE is_active = 1 AND face_encoding IS NOT NULL')
            student_rows = cursor.fetchall()
            conn.close()
            
            print(f"🔍 Found {len(student_rows)} students with face encodings (raw SQL)")
            for row in student_rows:
                print(f"   - {row[1]} ({row[2]})")
            
            # Convert to student objects for compatibility
            students = []
            for row in student_rows:
                student_data = {
                    'id': row[0],
                    'name': row[1], 
                    'roll_number': row[2],
                    'face_encoding': row[3]
                }
                students.append(student_data)
                
        except Exception as e:
            print(f"❌ Raw SQL query failed: {e}")
            # Fallback to SQLAlchemy
            students = Student.query.filter(
                Student.is_active == True,
                Student.face_encoding.isnot(None)
            ).all()
            print(f"🔍 Found {len(students)} students with face encodings (SQLAlchemy fallback)")
        
        # Prepare known faces database
        known_faces = []
        for student in students:
            try:
                # Handle both dictionary and SQLAlchemy object formats
                if isinstance(student, dict):
                    encoding = np.frombuffer(student['face_encoding'], dtype=np.float32)
                    known_faces.append({
                        'id': student['id'],
                        'name': student['name'],
                        'roll_number': student['roll_number'],
                        'class_name': student.get('class_name', ''),
                        'encoding': encoding
                    })
                else:
                    encoding = np.frombuffer(student.face_encoding, dtype=np.float32)
                    known_faces.append({
                        'id': student.id,
                        'name': student.name,
                        'roll_number': student.roll_number,
                        'class_name': getattr(student, 'class_name', ''),
                        'encoding': encoding
                    })
            except Exception as e:
                student_name = student['name'] if isinstance(student, dict) else student.name
                print(f"Error loading encoding for {student_name}: {e}")
        
        # Identify faces
        print(f"🎯 Attempting to identify faces in image...")
        print(f"📊 Known faces loaded: {len(known_faces)}")
        for kf in known_faces:
            print(f"   - {kf['name']} ({kf['roll_number']}) - Encoding shape: {kf['encoding'].shape}")
        
        identified_faces = face_rec.identify_faces(image, known_faces)
        print(f"🔍 MediaPipe returned {len(identified_faces)} identified faces")
        
        # Debug each face result
        for i, face in enumerate(identified_faces):
            print(f"   Face {i+1}: bbox={face.get('bbox')}, confidence={face.get('confidence', 0):.3f}, similarity={face.get('similarity', 0):.3f}, identified={face.get('identified', False)}")
        
        # Debug identification results and mark attendance
        for i, face in enumerate(identified_faces):
            if face.get('identified') and face.get('student_info'):
                student_info = face['student_info']
                print(f"✅ Face {i+1} identified as: {student_info['name']} ({student_info['roll_number']}) - Confidence: {face.get('similarity', 0):.2f}")
                
                # Mark attendance automatically
                try:
                    print(f"📝 Marking attendance for {student_info['name']} ({student_info['roll_number']})")
                    
                    # Create fresh database connection for attendance
                    attendance_conn = sqlite3.connect('attendance_enhanced.db')
                    attendance_cursor = attendance_conn.cursor()
                    
                    # Check if already marked today
                    attendance_cursor.execute("""
                        SELECT id FROM attendance 
                        WHERE student_id = ? AND date = DATE('now')
                    """, (student_info['roll_number'],))
                    
                    if attendance_cursor.fetchone():
                        print(f"ℹ️ Attendance already marked today for {student_info['name']}")
                    else:
                        # Mark new attendance
                        attendance_cursor.execute("""
                            INSERT INTO attendance (student_id, date, timestamp, status)
                            VALUES (?, DATE('now'), DATETIME('now'), 'Present')
                        """, (student_info['roll_number'],))
                        attendance_conn.commit()
                        print(f"✅ Attendance marked successfully for {student_info['name']} at {datetime.now().strftime('%H:%M:%S')}")
                    
                    attendance_conn.close()
                        
                except Exception as e:
                    print(f"❌ Failed to mark attendance for {student_info['name']}: {e}")
                    
            else:
                print(f"❌ Face {i+1} not identified - Best similarity: {face.get('similarity', 0):.2f}")
        
        # Format results
        results = []
        for face in identified_faces:
            face_result = {
                'bbox': face['bbox'],
                'confidence': float(face['confidence']),
                'similarity': float(face['similarity']),
                'identified': face['identified'],
                'student_info': face['student_info']
            }
            results.append(face_result)
        
        return jsonify({
            'success': True,
            'faces_detected': len(identified_faces),
            'identified_faces': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Processing error: {str(e)}'
        })

@app.route('/api/check_attendance_today/<int:student_id>')
def api_check_attendance_today(student_id):
    """Check if student attendance is already marked today"""
    today = date.today()
    attendance = Attendance.query.filter_by(
        student_id=student_id,
        date=today
    ).first()
    
    return jsonify({
        'already_marked': attendance is not None,
        'status': attendance.status if attendance else None,
        'method': attendance.method if attendance else None
    })

@app.route('/api/attendance_stats')
def api_attendance_stats():
    """Get current attendance statistics"""
    today = date.today()
    
    # Get today's attendance
    today_attendance = Attendance.query.filter(Attendance.date == today).all()
    present_today = sum(1 for record in today_attendance if record.status == 'Present')
    
    # Get total active students
    total_students = Student.query.filter(Student.is_active == True).count()
    
    stats = {
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': total_students - present_today,
        'attendance_percentage': (present_today / total_students * 100) if total_students > 0 else 0
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    # Import OpenCV for face recognition
    if FACE_RECOGNITION_AVAILABLE:
        import cv2
    
    try:
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️  Database setup warning: {e}")
    
    print(f"🚀 Enhanced Rural School Attendance System Starting...")
    print(f"📊 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"📸 Face Recognition: {'✅ Available' if FACE_RECOGNITION_AVAILABLE else '❌ Not Available'}")
    print(f"💾 Photo Storage: Database BLOB + File Backup")
    
    app.run(debug=True, host='0.0.0.0', port=5000)