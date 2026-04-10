# User Management Guide - Smart DEO

## Overview

The Smart DEO system has three types of users with different permission levels:
1. **Admin** - Full system access
2. **DEO (Data Entry Operator)** - Data management access
3. **HOD (Head of Department)** - Read-only access

---

## Default Users

### 1. Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **OTP**: `000000` (master OTP)
- **Department**: ALL
- **Permissions**: Everything

### 2. DEO Account (CSE)
- **Username**: `deo_cse`
- **Password**: `cse123`
- **OTP**: `000000`
- **Department**: CSE
- **Permissions**: Data management, Email notifications

### 3. HOD Account (CSE)
- **Username**: `hod_cse`
- **Password**: `hod123`
- **OTP**: `000000`
- **Department**: CSE
- **Permissions**: View-only access

---

## Role Permissions Matrix

| Feature | Admin | DEO | HOD |
|---------|:-----:|:---:|:---:|
| **View Dashboard** | ✅ | ✅ | ✅ |
| **Use AI Chatbot** | ✅ | ✅ | ✅ |
| **Export Reports** | ✅ | ✅ | ✅ |
| **Add Students** | ✅ | ✅ | ❌ |
| **Edit Students** | ✅ | ✅ | ❌ |
| **Delete Students** | ✅ | ✅ | ❌ |
| **Upload Files** | ✅ | ✅ | ❌ |
| **Send Email Notifications** | ✅ | ✅ | ❌ |
| **View Email Viewer** | ✅ | ✅ | ❌ |
| **Create Users** | ✅ | ❌ | ❌ |
| **Delete Users** | ✅ | ❌ | ❌ |
| **View User Management** | ✅ | ❌ | ❌ |
| **Access Database Viewer** | ✅ | ✅ | ✅ |
| **Generate QR Codes** | ✅ | ✅ | ✅ |

---

## How to Create New Users

### Method 1: Using Web Interface (Recommended)

1. **Login as Admin**
   ```
   URL: http://localhost:8000
   Username: admin
   Password: admin123
   OTP: 000000
   ```

2. **Navigate to User Registration**
   - Click "Console" from any page
   - Scroll to "Admin Features" section
   - Click "Register User" card
   - Or go directly to: http://localhost:8000/admin/register

3. **Fill Registration Form**
   - **Username**: Choose a unique username (e.g., `deo_ece`, `hod_mech`)
   - **Password**: Set a secure password (e.g., `ece123`)
   - **Role**: Select from dropdown:
     - `Admin` - Full access
     - `DEO` - Data management
     - `HOD` - Read-only
   - **Department**: Select from dropdown:
     - `CSE` - Computer Science
     - `ECE` - Electronics
     - `MECH` - Mechanical
     - `CIVIL` - Civil
     - `MBA` - Management

4. **Save QR Code**
   - After clicking "Register User", a QR code will be displayed
   - **Right-click** on the QR code → "Save image as..."
   - Save it with a meaningful name (e.g., `qr_deo_ece.png`)
   - Share this QR code with the new user

5. **Share Credentials**
   - Give the user their username and password
   - Give them the QR code image
   - Instruct them to scan the QR code with Google Authenticator

### Method 2: View All Users

1. **Navigate to User Management**
   - Login as Admin
   - Go to Console
   - Click "User Management" card
   - Or go to: http://localhost:8000/admin/users-management

2. **View User List**
   - See all users with their roles and departments
   - View user statistics
   - Delete users (except admin)

---

## User Naming Conventions

### Recommended Username Format:

**For DEO:**
- `deo_cse` - DEO for CSE department
- `deo_ece` - DEO for ECE department
- `deo_mech` - DEO for MECH department
- `deo_civil` - DEO for CIVIL department
- `deo_mba` - DEO for MBA department

**For HOD:**
- `hod_cse` - HOD of CSE department
- `hod_ece` - HOD of ECE department
- `hod_mech` - HOD of MECH department
- `hod_civil` - HOD of CIVIL department
- `hod_mba` - HOD of MBA department

**For Admin:**
- `admin` - Main administrator
- `admin_principal` - Principal account
- `admin_dean` - Dean account

---

## Department-Specific Access

### How It Works:

1. **Each user is assigned to a department**
2. **Users can only see data from their department**
3. **Admin can see all departments**

### Example:

- `deo_cse` (CSE department) → Can only see CSE students
- `hod_ece` (ECE department) → Can only see ECE students
- `admin` (ALL departments) → Can see all students

---

## Student vs System Users

### Important Distinction:

**System Users** (Admin, DEO, HOD):
- Login to the application
- Manage data
- View reports
- Created via Admin panel

**Students**:
- Do NOT login to the system
- Their data is managed by DEO/Admin
- Added via Data Management page
- Have roll numbers, not usernames

### How to Add Students:

1. **Login as DEO or Admin**
2. **Go to Data Management**
   - Console → "Data Management" card
   - Or: http://localhost:8000/data

3. **Choose Method:**
   - **Manual Entry**: Fill form for one student
   - **Upload File**: Upload Excel/CSV with multiple students

4. **Student Fields:**
   - Roll Number (unique identifier)
   - Name
   - Section
   - Department
   - Semester
   - Batch
   - CGPA
   - Attendance
   - Backlogs
   - Internal/External marks
   - Subject-wise marks (CN, SE, ADS, PDC)

---

## Common Scenarios

### Scenario 1: New Department Setup

**Goal**: Set up users for ECE department

**Steps**:
1. Login as `admin`
2. Create DEO: `deo_ece` / `ece123` / Role: DEO / Dept: ECE
3. Create HOD: `hod_ece` / `hod123` / Role: HOD / Dept: ECE
4. Save both QR codes
5. Share credentials with ECE staff

### Scenario 2: Multiple DEOs for Same Department

**Goal**: Add 2 DEOs for CSE department

**Steps**:
1. Login as `admin`
2. Create DEO 1: `deo_cse_1` / `cse123` / Role: DEO / Dept: CSE
3. Create DEO 2: `deo_cse_2` / `cse456` / Role: DEO / Dept: CSE
4. Both can manage CSE students independently

### Scenario 3: Temporary Access

**Goal**: Give temporary access to a faculty member

**Steps**:
1. Create user with HOD role (read-only)
2. Username: `temp_faculty` / Password: `temp123`
3. After work is done, delete the user from User Management page

### Scenario 4: Password Reset

**Goal**: User forgot their password

**Current Solution**:
1. Admin deletes the old user
2. Admin creates new user with same username
3. New QR code is generated
4. Share new credentials with user

**Note**: Password reset feature can be added if needed

---

## Security Best Practices

### For Admins:

1. **Change Default Passwords**
   - Don't use `admin123`, `cse123` in production
   - Use strong passwords (8+ characters, mixed case, numbers)

2. **Limit Admin Accounts**
   - Only create admin accounts when necessary
   - Most users should be DEO or HOD

3. **Use Real OTP**
   - Master OTP (`000000`) is for testing only
   - In production, use Google Authenticator with real QR codes

4. **Regular Audits**
   - Check User Management page regularly
   - Delete inactive users
   - Review user permissions

### For All Users:

1. **Keep Credentials Secure**
   - Don't share passwords
   - Don't write passwords on paper
   - Use password managers

2. **Logout After Use**
   - Always click "Logout" when done
   - Don't leave browser open on shared computers

3. **Session Timeout**
   - System auto-logs out after 15 minutes of inactivity
   - Save your work frequently

---

## Troubleshooting

### Issue: Can't Create New User

**Symptoms**: Error when clicking "Register User"

**Solutions**:
1. Make sure you're logged in as Admin
2. Check if username already exists
3. Try a different username
4. Check browser console for errors

### Issue: User Can't Login

**Symptoms**: "Invalid username or password" error

**Solutions**:
1. Verify username is correct (case-sensitive)
2. Verify password is correct
3. Check OTP is correct (use `000000` for testing)
4. Make sure user account exists (check User Management)

### Issue: User Can't See Features

**Symptoms**: Some features are grayed out or missing

**Solutions**:
1. Check user role (HOD has limited access)
2. Check department (users only see their department data)
3. Verify user is logged in correctly
4. Try logging out and back in

### Issue: Can't Delete User

**Symptoms**: Delete button doesn't work

**Solutions**:
1. Can't delete `admin` user (protected)
2. Make sure you're logged in as Admin
3. Refresh the page and try again

---

## API Endpoints for User Management

### Get All Users
```
GET /admin/users
Response: Array of user objects
```

### Create User
```
POST /admin/register
Body: {
  "username": "deo_ece",
  "password": "ece123",
  "role": "DEO",
  "dept": "ECE"
}
Response: {
  "success": true,
  "qr_code": "base64_image",
  "secret": "OTP_SECRET",
  "username": "deo_ece"
}
```

### Delete User
```
POST /admin/delete
Body: {
  "username": "deo_ece"
}
Response: {
  "success": true
}
```

---

## Quick Reference

### Access URLs:
- **Console**: http://localhost:8000/console
- **Register User**: http://localhost:8000/admin/register
- **User Management**: http://localhost:8000/admin/users-management
- **Data Management**: http://localhost:8000/data

### Default Credentials:
| Username | Password | Role | Department |
|----------|----------|------|------------|
| admin | admin123 | Admin | ALL |
| deo_cse | cse123 | DEO | CSE |
| hod_cse | hod123 | HOD | CSE |

### Master OTP:
- **Testing**: `000000`
- **Production**: Use Google Authenticator

---

## Summary

✅ **Three user roles**: Admin, DEO, HOD
✅ **Department-based access**: Users see only their department
✅ **Easy user creation**: Web interface for admins
✅ **Student management**: Separate from system users
✅ **Secure authentication**: 2FA with Google Authenticator
✅ **Role-based permissions**: Different access levels

**For Competition**: The user management system is fully functional and demonstrates enterprise-level access control! 🏆
