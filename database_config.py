"""
Enhanced Database Configuration for Rural School Attendance System
Supports multiple SQL databases: SQLite, MySQL, PostgreSQL
Enhanced photo storage with BLOB support and metadata
"""

import os
from datetime import datetime

class DatabaseConfig:
    """Database configuration for different SQL backends"""
    
    # Base configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'rural-school-attendance-secret-key-2025'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Photo storage options
    STORE_PHOTOS_IN_DB = True  # Store photos as BLOB in database
    STORE_PHOTOS_ON_DISK = True  # Also keep file copies for backup
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in DatabaseConfig.ALLOWED_EXTENSIONS

class SQLiteConfig(DatabaseConfig):
    """SQLite configuration - Default for rural schools (no server needed)"""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///attendance_enhanced.db'
    DB_TYPE = 'sqlite'

class MySQLConfig(DatabaseConfig):
    """MySQL configuration - For schools with dedicated servers"""
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'attendance_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'secure_password_2025'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'rural_attendance'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}'
    DB_TYPE = 'mysql'

class PostgreSQLConfig(DatabaseConfig):
    """PostgreSQL configuration - For advanced setups"""
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST') or 'localhost'
    POSTGRES_USER = os.environ.get('POSTGRES_USER') or 'attendance_user'
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD') or 'secure_password_2025'
    POSTGRES_DB = os.environ.get('POSTGRES_DB') or 'rural_attendance'
    
    SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}'
    DB_TYPE = 'postgresql'

# Configuration selection
def get_config():
    """Get database configuration based on environment"""
    db_type = os.environ.get('DB_TYPE', 'sqlite').lower()
    
    if db_type == 'mysql':
        return MySQLConfig
    elif db_type == 'postgresql':
        return PostgreSQLConfig
    else:
        return SQLiteConfig  # Default for rural schools

# Database connection test
def test_database_connection(app):
    """Test database connection and create tables if needed"""
    try:
        with app.app_context():
            from flask_sqlalchemy import SQLAlchemy
            db = SQLAlchemy(app)
            
            # Test connection
            db.session.execute('SELECT 1')
            db.session.commit()
            
            print(f"✅ Database connection successful: {app.config['SQLALCHEMY_DATABASE_URI']}")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

# Database initialization
def init_database(app, db):
    """Initialize database with enhanced tables"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Check if we need to add sample data
            from models_enhanced import Student, Attendance, DailyCode, PhotoMetadata
            
            student_count = Student.query.count()
            print(f"📊 Database initialized - {student_count} students found")
            
            # Create indexes for better performance
            create_database_indexes(db)
            
            return True
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            return False

def create_database_indexes(db):
    """Create database indexes for better performance"""
    try:
        # Index for attendance queries by date
        db.session.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_date 
            ON attendance(date);
        """)
        
        # Index for student roll number searches
        db.session.execute("""
            CREATE INDEX IF NOT EXISTS idx_student_roll 
            ON student(roll_number);
        """)
        
        # Index for daily codes by date
        db.session.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_code_date 
            ON daily_code(date);
        """)
        
        db.session.commit()
        print("✅ Database indexes created successfully")
        
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")

# Database migration utilities
class DatabaseMigration:
    """Handle database migrations and upgrades"""
    
    @staticmethod
    def backup_database(app):
        """Create database backup"""
        if app.config.get('DB_TYPE') == 'sqlite':
            import shutil
            from datetime import datetime
            
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{db_path}"
            
            try:
                shutil.copy2(db_path, backup_path)
                print(f"✅ Database backup created: {backup_path}")
                return backup_path
            except Exception as e:
                print(f"❌ Backup failed: {e}")
                return None
    
    @staticmethod
    def migrate_photos_to_db(app, db):
        """Migrate existing photo files to database BLOB storage"""
        with app.app_context():
            from models_enhanced import Student, PhotoMetadata
            
            students = Student.query.all()
            migrated = 0
            
            for student in students:
                if student.photo_path and not student.photo_blob:
                    try:
                        # Read photo file
                        full_path = os.path.join('static', student.photo_path.lstrip('/'))
                        if os.path.exists(full_path):
                            with open(full_path, 'rb') as f:
                                photo_data = f.read()
                            
                            # Store in database
                            student.photo_blob = photo_data
                            
                            # Create metadata
                            metadata = PhotoMetadata(
                                student_id=student.id,
                                filename=os.path.basename(full_path),
                                file_size=len(photo_data),
                                mime_type='image/jpeg'
                            )
                            db.session.add(metadata)
                            migrated += 1
                    
                    except Exception as e:
                        print(f"⚠️ Failed to migrate photo for {student.name}: {e}")
            
            db.session.commit()
            print(f"✅ Migrated {migrated} photos to database")