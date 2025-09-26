@echo off
echo =====================================================
echo    GROUP PHOTO ATTENDANCE SYSTEM
echo    Perfect for Rural Schools!
echo =====================================================
echo.

if not exist "attendance_env" (
    echo Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

call attendance_env\Scripts\activate.bat

echo 📸 GROUP PHOTO ATTENDANCE - The Smart Solution!
echo.
echo ✅ Take ONE photo of entire class
echo ✅ System identifies ALL students automatically  
echo ✅ 90%+ students marked in 2-3 seconds
echo ✅ Manual backup for missed students
echo ✅ No RFID cards to lose or share
echo ✅ Works with any camera/smartphone
echo.
echo Available systems:
echo 1. GROUP PHOTO System (RECOMMENDED) - app_group_photo.py
echo 2. Individual Recognition - app.py  
echo 3. Secure Manual System - app_secure_rural.py
echo.
echo Starting GROUP PHOTO ATTENDANCE SYSTEM...
echo Server starting at http://localhost:5000
echo.
echo 🎯 Perfect for rural schools - combines speed with flexibility!
echo 📚 See GROUP_PHOTO_GUIDE.md for complete instructions
echo.
echo Press Ctrl+C to stop the server
echo.

python app_group_photo.py