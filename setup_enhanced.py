#!/usr/bin/env python3
"""
Setup script for Enhanced Rural School Attendance System
Configures SQL database with photo BLOB storage
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_header():
    """Print setup header"""
    print("=" * 60)
    print("Enhanced Rural School Attendance System Setup")
    print("SQL Database with Photo BLOB Storage")
    print("=" * 60)

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version OK: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    
    requirements_file = "requirements_simple.txt"
    
    if not os.path.exists(requirements_file):
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "static/uploads",
        "static/images", 
        "instance",
        "backups",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    return True

def setup_database():
    """Set up the database"""
    print("\n🗄️ Setting up database...")
    
    try:
        # Import our models
        from models_enhanced import db, Student, Attendance, DailyCode, PhotoMetadata, AttendanceSession
        from app_enhanced_sql import create_app
        
        # Create app and initialize database
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Create indexes for better performance
            create_indexes(db)
            print("✅ Database indexes created")
            
            # Test database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            print("✅ Database connection test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_indexes(db):
    """Create database indexes for better performance"""
    try:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_student_roll ON student(roll_number);",
            "CREATE INDEX IF NOT EXISTS idx_student_active ON student(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_daily_code_date ON daily_code(date);",
            "CREATE INDEX IF NOT EXISTS idx_photo_metadata_student ON photo_metadata(student_id);"
        ]
        
        from sqlalchemy import text
        for index_sql in indexes:
            db.session.execute(text(index_sql))
        
        db.session.commit()
        
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")

def create_config_file():
    """Create configuration file"""
    print("\n⚙️ Creating configuration...")
    
    config_content = '''"""
Configuration for Enhanced Rural School Attendance System
"""

import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'enhanced-rural-school-attendance-2025'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///attendance_enhanced.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Photo storage settings
    STORE_PHOTOS_IN_DB = True
    STORE_PHOTOS_ON_DISK = True
    
    # Face recognition settings
    FACE_RECOGNITION_ENABLED = True
    FACE_CONFIDENCE_THRESHOLD = 0.6
    
    # Database settings
    DATABASE_POOL_SIZE = 10
    DATABASE_POOL_TIMEOUT = 30
    DATABASE_POOL_RECYCLE = 3600
    
    # Security settings
    DAILY_CODE_MAX_USAGE = 1000
    SESSION_TIMEOUT = 3600
    
    # Backup settings
    AUTO_BACKUP_ENABLED = True
    BACKUP_RETENTION_DAYS = 30
    
    # Logging settings
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/attendance.log'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Production database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
'''
    
    with open('config_enhanced.py', 'w') as f:
        f.write(config_content)
    
    print("✅ Configuration file created")
    return True

def create_startup_script():
    """Create startup script"""
    print("\n🚀 Creating startup script...")
    
    startup_content = '''@echo off
echo Starting Enhanced Rural School Attendance System...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if required files exist
if not exist "app_enhanced_sql.py" (
    echo app_enhanced_sql.py not found
    pause
    exit /b 1
)

REM Set environment variables
set FLASK_APP=app_enhanced_sql.py
set FLASK_ENV=development

echo Starting Flask application...
python app_enhanced_sql.py

pause
'''
    
    with open('start_enhanced.bat', 'w') as f:
        f.write(startup_content)
    
    print("✅ Startup script created: start_enhanced.bat")
    return True

def test_system():
    """Test the system components"""
    print("\n🧪 Testing system components...")
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Database connection
    try:
        from app_enhanced_sql import create_app
        app = create_app()
        with app.app_context():
            from models_enhanced import db
            db.session.execute('SELECT 1')
        print("✅ Test 1/5: Database connection")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1/5: Database connection failed - {e}")
    
    # Test 2: Face recognition
    try:
        from mediapipe_face_recognition import MediaPipeFaceRecognition
        face_rec = MediaPipeFaceRecognition()
        print("✅ Test 2/5: Face recognition system")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2/5: Face recognition failed - {e}")
    
    # Test 3: Image processing
    try:
        import cv2
        import numpy as np
        from PIL import Image
        print("✅ Test 3/5: Image processing libraries")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3/5: Image processing failed - {e}")
    
    # Test 4: Directory structure
    required_dirs = ["static/uploads", "instance", "backups", "logs"]
    dirs_exist = all(os.path.exists(d) for d in required_dirs)
    if dirs_exist:
        print("✅ Test 4/5: Directory structure")
        tests_passed += 1
    else:
        print("❌ Test 4/5: Directory structure incomplete")
    
    # Test 5: Configuration
    try:
        from config_enhanced import config
        print("✅ Test 5/5: Configuration system")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5/5: Configuration failed - {e}")
    
    print(f"\n📊 System Tests: {tests_passed}/{total_tests} passed")
    return tests_passed == total_tests

def main():
    """Main setup function"""
    print_header()
    
    # Setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories),
        ("Setting up database", setup_database),
        ("Creating configuration", create_config_file),
        ("Creating startup script", create_startup_script),
        ("Testing system", test_system)
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        print(f"\n▶️ {step_name}...")
        try:
            if step_function():
                success_count += 1
            else:
                print(f"❌ {step_name} failed")
                break
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
            break
    
    # Final results
    print("\n" + "=" * 60)
    if success_count == len(steps):
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python app_enhanced_sql.py")
        print("2. Open: http://127.0.0.1:5000")
        print("3. Start adding students with photos")
        print("\nOr use the startup script: start_enhanced.bat")
    else:
        print(f"⚠️ Setup partially completed: {success_count}/{len(steps)} steps")
        print("\nPlease check the error messages above and try again.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()