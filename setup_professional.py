"""
Professional Face Recognition System Setup
Installs and configures the professional face recognition system
"""

import subprocess
import sys
import os
import sqlite3
from datetime import datetime

def install_requirements():
    """Install required packages"""
    print("📦 Installing professional face recognition requirements...")
    
    try:
        # Install basic requirements first
        basic_packages = [
            'torch', 'torchvision', 'opencv-python', 'Pillow', 
            'scikit-learn', 'matplotlib', 'seaborn', 'pandas', 'tqdm'
        ]
        
        for package in basic_packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        # Install facenet-pytorch
        print("Installing facenet-pytorch...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "facenet-pytorch"])
        
        # Try to install dlib (may require Visual Studio Build Tools on Windows)
        print("Installing dlib (may take a while)...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "dlib"])
            print("✅ Dlib installed successfully")
        except subprocess.CalledProcessError:
            print("⚠️ Dlib installation failed. Some features may not work optimally.")
            print("   Install Visual Studio Build Tools for full functionality.")
        
        print("✅ All packages installed successfully!")
        
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False
    
    return True

def setup_database():
    """Setup database for professional system"""
    print("🗄️ Setting up professional database schema...")
    
    try:
        conn = sqlite3.connect('attendance_enhanced.db')
        cursor = conn.cursor()
        
        # Add professional columns if they don't exist
        try:
            cursor.execute('ALTER TABLE student ADD COLUMN face_quality FLOAT DEFAULT 0.0')
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute('ALTER TABLE student ADD COLUMN embedding_version INTEGER DEFAULT 1')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE attendance ADD COLUMN recognition_method VARCHAR(50) DEFAULT "basic"')
        except sqlite3.OperationalError:
            pass
        
        # Create professional settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_recognition_settings (
                id INTEGER PRIMARY KEY,
                similarity_threshold FLOAT DEFAULT 0.6,
                confidence_threshold FLOAT DEFAULT 0.8,
                model_version VARCHAR(50) DEFAULT "v1.0",
                last_training_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default settings
        cursor.execute('SELECT COUNT(*) FROM face_recognition_settings')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO face_recognition_settings 
                (similarity_threshold, confidence_threshold, model_version, last_training_date)
                VALUES (0.6, 0.8, "v1.0", ?)
            ''', (datetime.now(),))
        
        conn.commit()
        conn.close()
        
        print("✅ Database schema updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

def test_installation():
    """Test if all components are working"""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        import torch
        import cv2
        import numpy as np
        from PIL import Image
        import sklearn
        import matplotlib.pyplot as plt
        
        print("✅ Basic libraries imported successfully")
        
        # Test PyTorch
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"✅ PyTorch working on device: {device}")
        
        # Test OpenCV
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera access working")
            cap.release()
        else:
            print("⚠️ Camera not accessible")
        
        # Test facenet-pytorch
        try:
            from facenet_pytorch import MTCNN, InceptionResnetV1
            print("✅ FaceNet-PyTorch imported successfully")
        except ImportError:
            print("❌ FaceNet-PyTorch not available")
            return False
        
        # Test professional system
        try:
            from professional_face_recognition import ProfessionalFaceRecognizer
            recognizer = ProfessionalFaceRecognizer()
            print("✅ Professional face recognition system initialized")
        except Exception as e:
            print(f"❌ Professional system test failed: {e}")
            return False
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    print("📝 Creating sample configuration files...")
    
    try:
        # Create configuration file
        config = {
            "model_settings": {
                "similarity_threshold": 0.6,
                "confidence_threshold": 0.8,
                "device": "auto"
            },
            "training_settings": {
                "augment_data": True,
                "validation_split": 0.2,
                "batch_size": 32
            },
            "system_settings": {
                "max_faces_per_image": 10,
                "face_detection_confidence": 0.7,
                "attendance_auto_mark": True
            }
        }
        
        import json
        with open('professional_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration files created")
        return True
        
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Professional Face Recognition System Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher required")
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Step 1: Install requirements
    print("\n1. Installing requirements...")
    if not install_requirements():
        print("❌ Setup failed at package installation")
        return
    
    # Step 2: Setup database
    print("\n2. Setting up database...")
    if not setup_database():
        print("❌ Setup failed at database configuration")
        return
    
    # Step 3: Test installation
    print("\n3. Testing installation...")
    if not test_installation():
        print("❌ Setup failed at testing phase")
        return
    
    # Step 4: Create sample data
    print("\n4. Creating configuration files...")
    if not create_sample_data():
        print("⚠️ Warning: Could not create sample files")
    
    print("\n" + "=" * 50)
    print("✅ PROFESSIONAL SETUP COMPLETE!")
    print("\nNext steps:")
    print("1. Add students with photos using the web interface")
    print("2. Run training: python train_face_model.py")
    print("3. Test system: python professional_integration.py")
    print("4. Integrate with Flask app for production use")
    print("\nFor GPU acceleration, install CUDA-enabled PyTorch")

if __name__ == "__main__":
    main()