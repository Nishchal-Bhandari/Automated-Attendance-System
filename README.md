# Student Attendance System

A facial recognition-based attendance system designed for rural schools in India. This system helps automate attendance tracking, reducing manual effort and improving accuracy.

## 🎯 Problem Statement

Many rural schools in India rely on manual attendance systems, which are:
- Time-consuming for teachers
- Prone to human errors
- Lead to discrepancies in government reporting
- Affect resource allocation for schemes like mid-day meals

## 🚀 Solution

This system provides:
- **Automated Attendance**: Uses facial recognition to mark attendance
- **User-Friendly Interface**: Simple web interface for teachers and administrators
- **Low-Cost Solution**: Requires minimal infrastructure
- **Accurate Record Keeping**: Eliminates manual errors
- **Government Reporting**: Easy export of attendance data

## ✨ Features

### Core Features
- 📸 **Facial Recognition**: Automatic student identification using camera
- 👥 **Student Management**: Add students with photos and roll numbers
- 📊 **Attendance Tracking**: Real-time attendance marking and tracking
- 📈 **Reports & Analytics**: Daily, weekly, and monthly attendance reports
- 💾 **Data Export**: CSV export for government reporting

### Technical Features
- 🌐 **Web-Based Interface**: Access from any device with a browser
- 📱 **Responsive Design**: Works on computers, tablets, and smartphones
- 🔒 **Secure Database**: SQLite database for reliable data storage
- 🎥 **Camera Integration**: Direct camera access through web browser
- 📊 **Real-time Processing**: Instant face recognition and attendance marking

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Computer Vision**: OpenCV, face_recognition library
- **Image Processing**: PIL (Python Imaging Library)

## 📋 Prerequisites

- Python 3.8 or higher
- Web camera (built-in or external)
- Windows/macOS/Linux operating system
- Modern web browser with camera support

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

### 3. Access the System

Open your web browser and go to: `http://localhost:5000`

## 📖 User Guide

### For School Administrators

1. **Add Students**:
   - Go to "Add Student" section
   - Fill in student name and roll number
   - Upload a clear photo of the student
   - System will automatically create face encoding

2. **View Students**:
   - Check all registered students
   - Verify face encoding status
   - Monitor registration statistics

### For Teachers

1. **Mark Attendance**:
   - Click "Mark Attendance"
   - Start the camera
   - Students look at the camera one by one
   - System automatically recognizes and marks attendance

2. **View Reports**:
   - Access daily attendance reports
   - Filter by specific dates
   - Export data for government reporting

## 📱 System Requirements

### Minimum Requirements
- **Processor**: Dual-core 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **Camera**: VGA quality (640x480)
- **Internet**: Not required (works offline)

### Recommended Requirements
- **Processor**: Quad-core 2.5 GHz or higher
- **RAM**: 8 GB or higher
- **Storage**: 5 GB free space
- **Camera**: HD quality (1280x720) or higher

## 🎯 Target Beneficiaries

- **School Administrators**: Streamlined student management
- **Teachers**: Automated attendance, more teaching time
- **Students**: Accurate attendance records
- **Government**: Better data for education schemes
- **Parents**: Transparent attendance tracking

## 📊 Expected Impact

### Quantitative Benefits
- **Time Savings**: 80% reduction in attendance marking time
- **Accuracy**: 95%+ attendance accuracy (vs 70% manual)
- **Coverage**: Suitable for 50%+ of rural schools
- **Cost Effective**: <$100 total setup cost per school

### Qualitative Benefits
- Enhanced teaching time
- Improved government reporting
- Better resource allocation
- Increased administrative efficiency

## 🔧 Installation Guide

### Step 1: Clone or Download
```bash
git clone <repository-url>
cd student_attendance
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment (recommended)
python -m venv attendance_env

# Activate virtual environment
# On Windows:
attendance_env\Scripts\activate
# On macOS/Linux:
source attendance_env/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python app.py
```

### Step 5: Access the System
- Open browser: `http://localhost:5000`
- Start adding students and marking attendance!

## 🐛 Troubleshooting

### Common Issues

**Camera not working**:
- Check camera permissions in browser
- Ensure camera is not used by other applications
- Try refreshing the page

**Face not recognized**:
- Ensure good lighting conditions
- Student should face camera directly
- Remove sunglasses or face coverings
- Re-register student if persistent issues

**Installation errors**:
- Ensure Python 3.8+ is installed
- Install Visual Studio Build Tools (Windows)
- Use virtual environment to avoid conflicts

## 📝 File Structure

```
student_attendance/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── attendance.db         # SQLite database (created automatically)
├── templates/            # HTML templates
│   ├── base.html        # Base template
│   ├── index.html       # Home page
│   ├── add_student.html # Add student form
│   ├── students.html    # Student list
│   ├── attendance.html  # Attendance marking
│   └── reports.html     # Attendance reports
└── static/
    └── uploads/         # Student photos storage
```

## 🔐 Security Considerations

- Student photos are stored locally
- No data transmitted to external servers
- Face encodings are encrypted in database
- Regular backup recommended for important data

## 🚀 Future Enhancements

- **Multi-class Support**: Handle multiple classes/sections
- **Parent Notifications**: SMS/email alerts for attendance
- **Mobile App**: Native mobile application
- **Advanced Analytics**: Attendance trends and insights
- **Integration**: Connect with existing school management systems

## 📞 Support

For technical support or questions:
- Create an issue in the project repository
- Contact system administrator
- Refer to troubleshooting guide

## 📜 License

This project is developed for educational purposes and rural school implementation in India.

---

**Made with ❤️ for Rural Education in India**

*This system addresses real challenges faced by rural schools and contributes to the Digital India initiative in education.*