# 🔗 All Application Links & Routes

## 📱 Base URL
```
http://localhost:5000
```

---

## 🌐 Public Pages (No Login Required)

### 1. Home Page
```
GET http://localhost:5000/
```
- **Description**: Redirects to `/chat` if logged in, otherwise to `/login`
- **Access**: Public

### 2. Login Page
```
GET http://localhost:5000/login
```
- **Description**: User and admin login page
- **Access**: Public
- **Features**:
  - User login with OTP
  - Admin setup access
  - Department selection

### 3. Setup Page (Admin Credentials)
```
GET http://localhost:5000/setup
```
- **Description**: View default user credentials and generate QR codes
- **Access**: Public (requires master password)
- **Master Password**: `Admin@123`

---

## 🔐 Protected Pages (Login Required)

### 4. Chat Interface
```
GET http://localhost:5000/chat
```
- **Description**: Main chatbot interface for academic reports
- **Access**: All logged-in users (DEO, HOD, Admin)
- **Features**:
  - Quick report buttons
  - Natural language queries
  - Export to CSV/Excel/PDF
  - Session timer (15 minutes)

### 5. Data Management
```
GET http://localhost:5000/data
```
- **Description**: Student data management interface
- **Access**: DEO and Admin only
- **Features**:
  - Add/Edit/Delete students
  - Upload Excel files
  - Search students
  - View all student records

### 6. User Registration (Admin Only)
```
GET http://localhost:5000/admin/register
```
- **Description**: Register new users
- **Access**: Admin only
- **Features**:
  - Create new user accounts
  - Generate OTP QR codes
  - Set roles (DEO, HOD, Admin)

---

## 🔌 API Endpoints

### Authentication APIs

#### Login
```
POST http://localhost:5000/login
Content-Type: application/json

{
  "username": "deo_cse",
  "password": "cse123",
  "department": "CSE",
  "otp": "123456"
}
```

#### Logout
```
GET http://localhost:5000/logout
```

#### Get Current User
```
GET http://localhost:5000/api/me
```
- **Returns**: Current user info and last activity time

#### Database Status
```
GET http://localhost:5000/api/dbstatus
```
- **Returns**: Database connection status and student count

---

### Setup & QR Code APIs

#### Setup (Get All User Credentials)
```
POST http://localhost:5000/setup
Content-Type: application/json

{
  "password": "Admin@123"
}
```

#### Generate QR Code for User
```
POST http://localhost:5000/setup/qr
Content-Type: application/json

{
  "username": "deo_cse",
  "master": "Admin@123"
}
```

---

### Admin APIs

#### Register New User
```
POST http://localhost:5000/admin/register
Content-Type: application/json

{
  "username": "new_user",
  "password": "password123",
  "role": "DEO",
  "dept": "CSE"
}
```

#### List All Users
```
GET http://localhost:5000/admin/users
```
- **Access**: Admin only

#### Delete User
```
POST http://localhost:5000/admin/delete
Content-Type: application/json

{
  "username": "user_to_delete"
}
```

---

### Report APIs

#### Get Academic Report
```
POST http://localhost:5000/api/report
Content-Type: application/json

{
  "query": "Show attendance for CSE semester 3",
  "semester": "3",
  "batch": "2023-27"
}
```

**Example Queries:**
- `"Show attendance of 231FA00001"`
- `"Show students in section 1"`
- `"Show section-wise attendance"`
- `"Show subject performance analysis"`
- `"Show average marks"`
- `"Show students with backlogs"`
- `"Show CGPA distribution"`
- `"Show top performers"`

#### Export Report
```
POST http://localhost:5000/api/export
Content-Type: application/json

{
  "format": "csv",
  "data": [...student data...],
  "filename": "report.csv"
}
```
- **Formats**: `csv`, `excel`, `pdf`

---

### Data Management APIs

#### Get Students
```
GET http://localhost:5000/data/students?search=231FA
```
- **Query Params**: `search` (optional)

#### Add Student
```
POST http://localhost:5000/data/add
Content-Type: application/json

{
  "roll": "231FA00001",
  "name": "John Doe",
  "section": "SEC-1",
  "department": "CSE",
  "semester": "3",
  "batch": "2023-27",
  "cgpa": 8.5,
  "attendance": 85,
  "backlogs": 0,
  "internal": 40,
  "external": 75,
  "subjects": {
    "CN": {"attendance": 85, "internal": 40, "external": 75},
    "SE": {"attendance": 90, "internal": 45, "external": 80},
    "ADS": {"attendance": 80, "internal": 38, "external": 70},
    "PDC": {"attendance": 88, "internal": 42, "external": 78}
  }
}
```

#### Update Student
```
POST http://localhost:5000/data/update
Content-Type: application/json

{
  "roll": "231FA00001",
  "name": "John Doe Updated",
  "section": "SEC-1",
  ...
}
```

#### Delete Student
```
POST http://localhost:5000/data/delete
Content-Type: application/json

{
  "roll": "231FA00001"
}
```

#### Upload Excel File
```
POST http://localhost:5000/data/upload
Content-Type: multipart/form-data

file: [Excel file with student data]
```

---

## 📂 Static Files

### CSS
```
GET http://localhost:5000/static/modern-style.css
```

### JavaScript
```
GET http://localhost:5000/static/script.js
GET http://localhost:5000/static/theme-toggle.js
```

### Images
```
GET http://localhost:5000/static/images/university-bg.jpg
```

---

## 👥 Default User Accounts

### 1. DEO (Data Entry Operator)
```
Username: deo_cse
Password: cse123
Department: CSE
Role: DEO
```

### 2. HOD (Head of Department)
```
Username: hod_cse
Password: hod123
Department: CSE
Role: HOD
```

### 3. Admin
```
Username: admin
Password: admin123
Department: ALL
Role: Admin
```

---

## 🔑 Access Control

| Route | DEO | HOD | Admin |
|-------|-----|-----|-------|
| `/chat` | ✅ | ✅ | ✅ |
| `/data` | ✅ | ❌ | ✅ |
| `/admin/register` | ❌ | ❌ | ✅ |
| `/admin/users` | ❌ | ❌ | ✅ |
| `/data/add` | ✅ | ❌ | ✅ |
| `/data/update` | ✅ | ❌ | ✅ |
| `/data/delete` | ✅ | ❌ | ✅ |
| `/data/upload` | ✅ | ❌ | ✅ |

---

## 🚀 Quick Start Links

### For Testing:
1. **Login Page**: http://localhost:5000/login
2. **Setup Page**: http://localhost:5000/setup
3. **Chat Interface**: http://localhost:5000/chat (after login)
4. **Data Management**: http://localhost:5000/data (after login as DEO/Admin)

### For Development:
- **API Documentation**: The app uses FastAPI, but no auto-docs are exposed
- **Database**: MySQL on localhost with database name from `database.py`

---

## 📱 Mobile/Responsive

All pages are responsive and work on:
- Desktop (1920x1080+)
- Tablet (768px - 1024px)
- Mobile (320px - 767px)

---

## 🎨 Theme Support

All pages support:
- **Dark Mode** (default)
- **Light Mode** (toggle button in top-right)

Theme preference is saved in browser localStorage.

---

## ⏱️ Session Management

- **Session Timeout**: 15 minutes of inactivity
- **Session Timer**: Visible in sidebar (counts down from 15:00)
- **Auto Logout**: Redirects to `/login?reason=timeout` after timeout

---

## 📊 Report Types Supported

1. Student Lookup (by roll number)
2. Section Lookup (all students in a section)
3. Average Marks
4. Subject Performance Analysis
5. CGPA Distribution
6. Section-wise Attendance
7. Subject-wise Attendance
8. Department-wise Attendance
9. Top Performers / Toppers
10. Students with Backlogs
11. Low Attendance Students
12. Academic Risk Students
13. Subject-specific Reports (CN, SE, ADS, PDC)
14. Comparison Reports (section vs section)
15. Marks Distribution
16. Failure Rate Analysis

---

## 🔧 Configuration

- **Port**: 5000
- **Host**: 127.0.0.1 (localhost)
- **Reload**: Enabled (auto-reload on file changes)
- **Session Secret**: `deo_chatbot_secret_key_2024`
- **Master Password**: `Admin@123`

---

## 📝 Notes

- All API endpoints require authentication except `/login`, `/setup`, and static files
- OTP codes are 6 digits and valid for 60 seconds (±2 windows)
- Excel upload supports `.xlsx` files with specific column format
- Export supports CSV, Excel, and PDF formats
- Database uses MySQL with connection pooling

---

## ✅ Testing Checklist

- [ ] Login with DEO account
- [ ] Login with Admin account
- [ ] Generate QR codes from setup page
- [ ] Ask chatbot questions
- [ ] Export reports to CSV/Excel/PDF
- [ ] Add/Edit/Delete students (DEO/Admin)
- [ ] Upload Excel file
- [ ] Test session timeout (wait 15 minutes)
- [ ] Test theme toggle (light/dark mode)
- [ ] Test on mobile device

---

**Last Updated**: April 8, 2026
**Server**: FastAPI + Uvicorn
**Database**: MySQL
**Frontend**: Jinja2 + Vanilla JS + Modern CSS3
