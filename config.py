# Configuration file for Student Attendance System

# Database Configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///attendance.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Security Configuration
SECRET_KEY = 'your-secret-key-change-this-in-production'

# Upload Configuration
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Face Recognition Configuration
FACE_RECOGNITION_TOLERANCE = 0.6  # Lower = more strict, Higher = more lenient
FACE_DETECTION_MODEL = 'hog'  # 'hog' for CPU, 'cnn' for GPU (more accurate but slower)

# Application Configuration
DEBUG = True  # Set to False in production
HOST = '0.0.0.0'  # '127.0.0.1' for local only, '0.0.0.0' for network access
PORT = 5000

# School Information (for reports)
SCHOOL_NAME = "Sample Rural School"
SCHOOL_ADDRESS = "Village, District, State, India"
ACADEMIC_YEAR = "2024-25"

# Attendance Configuration
ATTENDANCE_WINDOW_START = "08:00"  # Start time for attendance marking
ATTENDANCE_WINDOW_END = "10:00"    # End time for attendance marking
AUTO_MARK_ABSENT = False  # Automatically mark absent students at end of day

# Backup Configuration
AUTO_BACKUP = True
BACKUP_INTERVAL_DAYS = 7  # Create backup every 7 days
BACKUP_LOCATION = "backups/"