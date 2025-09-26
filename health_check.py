"""
System Health Check Script
Run this script to verify all dependencies and system requirements
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_required_packages():
    """Check if all required packages are installed"""
    print("\n📦 Checking required packages...")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'opencv-python',
        'face_recognition',
        'pillow',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - Missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_camera_availability():
    """Check if camera is available"""
    print("\n📹 Checking camera availability...")
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("   ✅ Camera is working")
                cap.release()
                return True
            else:
                print("   ❌ Camera found but cannot capture frames")
                cap.release()
                return False
        else:
            print("   ❌ Cannot access camera")
            return False
    except ImportError:
        print("   ❌ OpenCV not installed - cannot test camera")
        return False
    except Exception as e:
        print(f"   ❌ Camera error: {str(e)}")
        return False

def check_disk_space():
    """Check available disk space"""
    print("\n💾 Checking disk space...")
    
    try:
        if platform.system() == "Windows":
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024**3)
            print(f"   💾 Free space: {free_gb:.2f} GB")
            
            if free_gb >= 2:
                print("   ✅ Sufficient disk space")
                return True
            else:
                print("   ❌ Low disk space - need at least 2GB")
                return False
        else:
            # For Linux/Mac
            statvfs = os.statvfs('.')
            free_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
            print(f"   💾 Free space: {free_gb:.2f} GB")
            
            if free_gb >= 2:
                print("   ✅ Sufficient disk space")
                return True
            else:
                print("   ❌ Low disk space - need at least 2GB")
                return False
    except Exception as e:
        print(f"   ⚠️  Could not check disk space: {str(e)}")
        return True  # Don't fail the check for this

def check_file_permissions():
    """Check if we have write permissions in the current directory"""
    print("\n📝 Checking file permissions...")
    
    try:
        test_file = "test_write_permission.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("   ✅ Write permissions OK")
        return True
    except Exception as e:
        print(f"   ❌ Cannot write files: {str(e)}")
        return False

def check_system_resources():
    """Check system resources (RAM)"""
    print("\n🖥️  Checking system resources...")
    
    try:
        import psutil
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024**3)
        available_gb = memory.available / (1024**3)
        
        print(f"   🧠 Total RAM: {total_gb:.2f} GB")
        print(f"   🧠 Available RAM: {available_gb:.2f} GB")
        
        if available_gb >= 2:
            print("   ✅ Sufficient RAM")
            return True
        else:
            print("   ⚠️  Low available RAM - may affect performance")
            return True  # Don't fail, just warn
    except ImportError:
        print("   ⚠️  psutil not installed - cannot check RAM")
        return True
    except Exception as e:
        print(f"   ⚠️  Could not check system resources: {str(e)}")
        return True

def main():
    """Run all health checks"""
    print("=" * 50)
    print("🏥 STUDENT ATTENDANCE SYSTEM - HEALTH CHECK")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        ("Python Version", check_python_version),
        ("File Permissions", check_file_permissions),
        ("Disk Space", check_disk_space),
        ("System Resources", check_system_resources),
    ]
    
    for check_name, check_function in checks:
        if not check_function():
            all_checks_passed = False
    
    # Check packages separately to provide installation help
    packages_ok, missing_packages = check_required_packages()
    if not packages_ok:
        all_checks_passed = False
    
    # Check camera
    camera_ok = check_camera_availability()
    if not camera_ok:
        print("\n⚠️  Camera issues detected. The system will work but attendance marking may not function properly.")
    
    # Final summary
    print("\n" + "=" * 50)
    if all_checks_passed and camera_ok:
        print("🎉 ALL CHECKS PASSED - SYSTEM READY!")
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Open browser: http://localhost:5000")
        print("3. Start adding students!")
    elif all_checks_passed:
        print("⚠️  BASIC CHECKS PASSED - CAMERA ISSUES DETECTED")
        print("\nThe system will start but camera functionality may not work.")
        print("Please check your camera and try again.")
    else:
        print("❌ SOME CHECKS FAILED - PLEASE FIX ISSUES ABOVE")
        
        if missing_packages:
            print(f"\nTo install missing packages:")
            print(f"pip install {' '.join(missing_packages)}")
    
    print("=" * 50)

if __name__ == "__main__":
    main()