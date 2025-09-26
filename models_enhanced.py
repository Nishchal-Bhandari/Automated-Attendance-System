"""
Enhanced Database Models for Rural School Attendance System
Supports photo storage in database (BLOB) and enhanced metadata
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import hashlib
import secrets
import base64

db = SQLAlchemy()

class Student(db.Model):
    """Enhanced Student model with photo BLOB storage"""
    __tablename__ = 'student'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    roll_number = db.Column(db.String(20), nullable=False, unique=True, index=True)
    class_name = db.Column(db.String(50), nullable=True)  # New: Class/Grade
    section = db.Column(db.String(10), nullable=True)     # New: Section A/B/C
    
    # Contact Information
    phone_number = db.Column(db.String(15), nullable=True)
    parent_name = db.Column(db.String(100), nullable=True)
    parent_phone = db.Column(db.String(15), nullable=True)  # New: Parent contact
    address = db.Column(db.Text, nullable=True)             # New: Address
    
    # Photo Storage (Enhanced)
    photo_path = db.Column(db.String(200), nullable=True)   # File path (backup)
    photo_blob = db.Column(db.LargeBinary, nullable=True)   # Photo data in database
    photo_hash = db.Column(db.String(64), nullable=True)    # SHA-256 hash for integrity
    
    # Face Recognition Data
    face_encoding = db.Column(db.LargeBinary, nullable=True) # Face encoding as binary data
    face_confidence = db.Column(db.Float, nullable=True)    # Recognition confidence
    
    # Security and Authentication
    secure_token = db.Column(db.String(100), nullable=True)
    qr_code_data = db.Column(db.Text, nullable=True)        # QR code for mobile attendance
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_attendance = db.Column(db.DateTime, nullable=True)  # Last attendance date
    
    # Status
    is_active = db.Column(db.Boolean, default=True)         # Active/Inactive student
    graduation_year = db.Column(db.Integer, nullable=True)   # Expected graduation
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    photo_metadata = db.relationship('PhotoMetadata', backref='student', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.name} ({self.roll_number})>'
    
    def generate_secure_token(self):
        """Generate a new secure token for the student"""
        self.secure_token = hashlib.sha256(
            f"{self.roll_number}{secrets.token_hex(16)}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:32]
    
    def set_photo_blob(self, photo_data):
        """Set photo data and calculate hash"""
        self.photo_blob = photo_data
        self.photo_hash = hashlib.sha256(photo_data).hexdigest()
    
    def get_photo_base64(self):
        """Get photo as base64 string for display"""
        if self.photo_blob:
            return base64.b64encode(self.photo_blob).decode('utf-8')
        return None
    
    def verify_photo_integrity(self):
        """Verify photo data integrity using hash"""
        if self.photo_blob and self.photo_hash:
            current_hash = hashlib.sha256(self.photo_blob).hexdigest()
            return current_hash == self.photo_hash
        return False
    
    def to_dict(self):
        """Convert student to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'roll_number': self.roll_number,
            'class_name': self.class_name,
            'section': self.section,
            'parent_name': self.parent_name,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'has_photo': bool(self.photo_blob),
            'has_face_encoding': bool(self.face_encoding)
        }

class PhotoMetadata(db.Model):
    """Metadata for student photos"""
    __tablename__ = 'photo_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    
    # File Information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=True)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(50), nullable=False)
    
    # Image Properties
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    format = db.Column(db.String(10), nullable=True)  # JPEG, PNG, etc.
    
    # Upload Information
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.String(100), nullable=True)  # Admin/Teacher name
    upload_method = db.Column(db.String(20), default='web')  # web, mobile, bulk
    
    # Processing Information
    is_processed = db.Column(db.Boolean, default=False)
    face_detected = db.Column(db.Boolean, default=False)
    processing_notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<PhotoMetadata {self.filename} for Student {self.student_id}>'

class Attendance(db.Model):
    """Enhanced Attendance model with more metadata"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False, index=True)
    
    # Date and Time
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    time_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_out = db.Column(db.DateTime, nullable=True)  # For tracking exit time
    
    # Attendance Details
    status = db.Column(db.String(20), nullable=False, default='Present')  # Present, Absent, Late
    method = db.Column(db.String(20), nullable=False, default='Manual')   # Manual, Camera, QR_Mobile, Photo_Upload
    confidence = db.Column(db.Float, nullable=True)  # Face recognition confidence
    
    # Verification and Security
    verification_code = db.Column(db.String(10), nullable=True)
    verified_by = db.Column(db.String(100), nullable=True)  # Teacher name
    
    # Location and Device Information
    device_info = db.Column(db.String(200), nullable=True)   # Device used for marking
    ip_address = db.Column(db.String(45), nullable=True)     # IP address
    location_info = db.Column(db.String(200), nullable=True) # GPS or location data
    
    # Additional Metadata
    notes = db.Column(db.Text, nullable=True)                # Special notes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure one attendance record per student per day
    __table_args__ = (db.UniqueConstraint('student_id', 'date', name='unique_attendance_per_day'),)
    
    def __repr__(self):
        return f'<Attendance {self.student.name if self.student else "Unknown"} on {self.date}>'
    
    def to_dict(self):
        """Convert attendance to dictionary"""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else 'Unknown',
            'date': self.date.isoformat() if self.date else None,
            'time_in': self.time_in.isoformat() if self.time_in else None,
            'time_out': self.time_out.isoformat() if self.time_out else None,
            'status': self.status,
            'method': self.method,
            'confidence': self.confidence,
            'verified_by': self.verified_by,
            'notes': self.notes
        }

class DailyCode(db.Model):
    """Enhanced Daily verification codes"""
    __tablename__ = 'daily_code'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True, index=True)
    daily_code = db.Column(db.String(10), nullable=False)
    
    # Enhanced Security
    code_hash = db.Column(db.String(64), nullable=True)      # Hash of the code
    usage_count = db.Column(db.Integer, default=0)           # How many times used
    max_usage = db.Column(db.Integer, default=1000)          # Maximum allowed usage
    
    # Validity
    valid_from = db.Column(db.DateTime, nullable=True)       # Valid from time
    valid_until = db.Column(db.DateTime, nullable=True)      # Valid until time
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100), nullable=True)    # Admin who generated
    
    def __repr__(self):
        return f'<DailyCode {self.daily_code} for {self.date}>'
    
    def generate_code_hash(self):
        """Generate hash for the daily code"""
        if self.daily_code:
            self.code_hash = hashlib.sha256(
                f"{self.daily_code}{self.date.isoformat()}".encode()
            ).hexdigest()
    
    def is_valid(self):
        """Check if the daily code is still valid"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.usage_count < self.max_usage and
            (not self.valid_from or now >= self.valid_from) and
            (not self.valid_until or now <= self.valid_until)
        )
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        if self.usage_count >= self.max_usage:
            self.is_active = False

class AttendanceSession(db.Model):
    """Track attendance sessions and bulk operations"""
    __tablename__ = 'attendance_session'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=False, unique=True, index=True)
    
    # Session Information
    session_date = db.Column(db.Date, nullable=False, default=date.today)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    
    # Session Details
    session_type = db.Column(db.String(20), nullable=False)  # daily, makeup, special
    conducted_by = db.Column(db.String(100), nullable=True)  # Teacher/Admin name
    method_used = db.Column(db.String(20), nullable=False)   # camera, photo_upload, manual
    
    # Statistics
    total_students = db.Column(db.Integer, default=0)
    present_count = db.Column(db.Integer, default=0)
    absent_count = db.Column(db.Integer, default=0)
    
    # Metadata
    notes = db.Column(db.Text, nullable=True)
    device_info = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<AttendanceSession {self.session_id} on {self.session_date}>'
    
    def generate_session_id(self):
        """Generate unique session ID"""
        self.session_id = hashlib.sha256(
            f"{datetime.utcnow().isoformat()}{secrets.token_hex(16)}".encode()
        ).hexdigest()[:32]

# Database utility functions
def create_sample_data():
    """Create sample data for testing"""
    # This will be called only in development/demo mode
    pass

def get_database_stats():
    """Get database statistics"""
    stats = {
        'total_students': Student.query.count(),
        'active_students': Student.query.filter_by(is_active=True).count(),
        'students_with_photos': Student.query.filter(Student.photo_blob.isnot(None)).count(),
        'total_attendance_records': Attendance.query.count(),
        'attendance_today': Attendance.query.filter_by(date=date.today()).count(),
        'total_photos': PhotoMetadata.query.count(),
        'active_daily_codes': DailyCode.query.filter_by(is_active=True).count()
    }
    return stats

def cleanup_old_data(days_to_keep=365):
    """Clean up old data (keep only specified number of days)"""
    from datetime import timedelta
    
    cutoff_date = date.today() - timedelta(days=days_to_keep)
    
    # Remove old attendance records
    old_attendance = Attendance.query.filter(Attendance.date < cutoff_date).all()
    for record in old_attendance:
        db.session.delete(record)
    
    # Remove old daily codes
    old_codes = DailyCode.query.filter(DailyCode.date < cutoff_date).all()
    for code in old_codes:
        db.session.delete(code)
    
    # Remove old sessions
    old_sessions = AttendanceSession.query.filter(AttendanceSession.session_date < cutoff_date).all()
    for session in old_sessions:
        db.session.delete(session)
    
    db.session.commit()
    return len(old_attendance) + len(old_codes) + len(old_sessions)