# Role-Based Access Control (RBAC) - Complete Guide

## Overview

Smart DEO implements comprehensive Role-Based Access Control (RBAC) to ensure proper security and data access management. Each role has specific permissions tailored to their responsibilities.

## Available Roles

### 1. Admin (Full Access)
**Description**: System administrators with complete control

**Permissions**:
- ✅ View all data
- ✅ Create/Edit/Delete students
- ✅ Upload bulk data
- ✅ Send email notifications
- ✅ View email logs
- ✅ Create/Manage users
- ✅ Access all features
- ✅ View database tables
- ✅ Generate QR codes

**Use Case**: System administrators, IT staff

### 2. DEO (Data Entry Officer)
**Description**: Full data management access

**Permissions**:
- ✅ View all data
- ✅ Create/Edit/Delete students
- ✅ Upload bulk data
- ✅ Send email notifications
- ✅ View email logs
- ❌ Create/Manage users
- ✅ Access most features
- ✅ View database tables

**Use Case**: Data entry staff, office administrators

### 3. HOD (Head of Department)
**Description**: Department heads with view and notification access

**Permissions**:
- ✅ View all data (read-only)
- ❌ Create/Edit/Delete students
- ❌ Upload bulk data
- ✅ Send email notifications
- ✅ View email logs
- ❌ Create/Manage users
- ✅ View reports and analytics
- ✅ Access chatbot

**Use Case**: Department heads, academic coordinators

### 4. Faculty (Teacher)
**Description**: Teachers with view-only access

**Permissions**:
- ✅ View all data (read-only)
- ❌ Create/Edit/Delete students
- ❌ Upload bulk data
- ❌ Send email notifications
- ❌ View email logs
- ❌ Create/Manage users
- ✅ View reports and analytics
- ✅ Access chatbot

**Use Case**: Teaching staff, faculty members

### 5. Student
**Description**: Students with limited view access

**Permissions**:
- ✅ View limited data (read-only)
- ❌ Create/Edit/Delete students
- ❌ Upload bulk data
- ❌ Send email notifications
- ❌ View email logs
- ❌ Create/Manage users
- ✅ View own data
- ✅ Access chatbot (limited)

**Use Case**: Students, learners

### 6. Others (View Only)
**Description**: External users with minimal access

**Permissions**:
- ✅ View limited data (read-only)
- ❌ Create/Edit/Delete students
- ❌ Upload bulk data
- ❌ Send email notifications
- ❌ View email logs
- ❌ Create/Manage users
- ✅ View reports (limited)
- ✅ Access chatbot (limited)

**Use Case**: External auditors, guests, observers

---

## Permission Matrix

| Feature | Admin | DEO | HOD | Faculty | Student | Others |
|---------|-------|-----|-----|---------|---------|--------|
| **View Data** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Create Students** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Edit Students** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Delete Students** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Upload Bulk Data** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Send Notifications** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **View Email Logs** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Create Users** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Manage Users** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Dashboard** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Use Chatbot** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Export Reports** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Database Viewer** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Setup/QR Codes** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## How to Create New Users

### Step 1: Login as Admin

Only Admin users can create new users.

1. Login with Admin credentials
2. Navigate to Console
3. Click "Register User" card

### Step 2: Fill Registration Form

**Required Fields:**
- **Username**: Unique identifier (e.g., `faculty_john`, `student_123`)
- **Password**: Strong password (min 8 characters)
- **Role**: Select from dropdown:
  - Admin (Full Access)
  - DEO (Data Entry Officer)
  - HOD (Head of Department)
  - Faculty (Teacher)
  - Student
  - Others (View Only)
- **Department**: CSE, ECE, MECH, CIVIL, MBA, or ALL

### Step 3: Generate QR Code

After registration:
1. QR code is automatically generated
2. User scans QR code with Google Authenticator
3. User can now login with username, password, and OTP

---

## Default Users

The system comes with 3 default users:

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Admin
- **Department**: ALL
- **OTP**: `000000` (master OTP)

### DEO Account
- **Username**: `deo_cse`
- **Password**: `cse123`
- **Role**: DEO
- **Department**: CSE
- **OTP**: `000000` (master OTP)

### HOD Account
- **Username**: `hod_cse`
- **Password**: `hod123`
- **Role**: HOD
- **Department**: CSE
- **OTP**: `000000` (master OTP)

---

## Access Control Examples

### Example 1: Faculty Member

**Scenario**: A faculty member wants to view student performance

**Access**:
- ✅ Can login to system
- ✅ Can view Console
- ✅ Can access Dashboard
- ✅ Can use Chatbot to query data
- ✅ Can view student lists
- ❌ Cannot edit student data
- ❌ Cannot send notifications
- ❌ Cannot upload files

**Workflow**:
1. Login with faculty credentials
2. Go to Console
3. Click "AI Chatbot"
4. Ask: "Show students in SEC-1"
5. View results (read-only)

### Example 2: HOD

**Scenario**: HOD wants to send low attendance alerts

**Access**:
- ✅ Can login to system
- ✅ Can view all data
- ✅ Can send email notifications
- ✅ Can view email logs
- ❌ Cannot edit student data
- ❌ Cannot create users

**Workflow**:
1. Login with HOD credentials
2. Go to Console
3. Click "Email Notifications"
4. Select students with low attendance
5. Send alerts to faculty

### Example 3: Student

**Scenario**: Student wants to check their own performance

**Access**:
- ✅ Can login to system
- ✅ Can view own data
- ✅ Can use Chatbot (limited)
- ❌ Cannot view other students' data
- ❌ Cannot edit any data
- ❌ Cannot send notifications

**Workflow**:
1. Login with student credentials
2. Go to Console
3. Click "AI Chatbot"
4. Ask: "Show my attendance" (filtered to own data)
5. View own results only

---

## Security Features

### 1. Session Management
- **Timeout**: 15 minutes (configurable)
- **Visual Timer**: Countdown in sidebar
- **Auto-Logout**: Automatic on timeout
- **Activity Tracking**: Updates on user interactions

### 2. Two-Factor Authentication (2FA)
- **Required**: For all users
- **Method**: Google Authenticator
- **Backup**: Master OTP for testing (`000000`)

### 3. Password Security
- **Hashing**: Werkzeug password hashing
- **Minimum Length**: 8 characters (recommended)
- **Storage**: Encrypted in database

### 4. Role Validation
- **Server-Side**: All permissions checked on server
- **Client-Side**: UI elements hidden based on role
- **API Protection**: Endpoints protected with decorators

---

## API Endpoints & Permissions

### Public Endpoints (No Auth Required)
- `GET /` - Home page (redirects to login)
- `GET /login` - Login page
- `POST /login` - Login authentication

### Authenticated Endpoints (All Roles)
- `GET /console` - Console page
- `GET /chat` - Chatbot page
- `GET /dashboard` - Dashboard page
- `POST /api/report` - Query reports
- `GET /api/me` - Get user info

### Write Access (Admin, DEO Only)
- `POST /data/add` - Add student
- `POST /data/update` - Update student
- `POST /data/delete` - Delete student
- `POST /data/upload` - Upload bulk data

### Notification Access (Admin, DEO, HOD)
- `GET /notifications` - Notifications page
- `POST /api/notifications/send` - Send notifications
- `POST /api/notifications/bulk-report` - Send bulk report
- `GET /emails/viewer` - View email logs

### Admin Only
- `GET /admin/register` - Register user page
- `POST /admin/register` - Create new user
- `GET /admin/users` - List all users
- `POST /admin/delete` - Delete user

---

## Best Practices

### For Administrators

1. **Create Specific Accounts**: Don't share admin credentials
2. **Use Appropriate Roles**: Assign minimum required permissions
3. **Regular Audits**: Review user access periodically
4. **Strong Passwords**: Enforce password policies
5. **Monitor Activity**: Check logs for suspicious activity

### For Users

1. **Secure Credentials**: Don't share username/password
2. **Logout Properly**: Always logout when done
3. **Report Issues**: Report unauthorized access immediately
4. **Use 2FA**: Always enable Google Authenticator
5. **Follow Policies**: Adhere to organization's data policies

### For Developers

1. **Server-Side Validation**: Always validate permissions on server
2. **Use Decorators**: Use `require_admin()`, `require_write_access()`, etc.
3. **Check Permissions**: Use `can_write()`, `can_send_notifications()`, etc.
4. **Audit Logs**: Log all sensitive operations
5. **Test Thoroughly**: Test all roles and permissions

---

## Troubleshooting

### Issue: User Can't Access Feature

**Check**:
1. User's role in database
2. Feature permissions for that role
3. Session is active (not expired)
4. User is logged in correctly

**Solution**:
- Verify role assignment
- Check permission matrix above
- Re-login if session expired
- Contact admin if role is incorrect

### Issue: Permission Denied Error

**Symptoms**:
- "403 Forbidden" error
- "Write access denied" message
- Feature grayed out

**Solution**:
- Check your role permissions
- Contact admin to upgrade role if needed
- Use view-only features instead

### Issue: Can't Create Users

**Symptoms**:
- "Admin only" error
- Register page not accessible

**Solution**:
- Only Admin can create users
- Login with Admin account
- Contact existing admin for help

---

## Future Enhancements

### Planned Features

1. **Custom Roles**: Create custom roles with specific permissions
2. **Department Isolation**: Restrict data access by department
3. **Audit Logs**: Track all user actions
4. **Permission Groups**: Group permissions for easier management
5. **Temporary Access**: Grant time-limited access
6. **API Keys**: Generate API keys for external integrations

---

## Quick Reference

### Permission Check Functions

```python
# In main.py

def require_login(request):
    """Require any authenticated user"""
    
def require_admin(request):
    """Require Admin role"""
    
def require_write_access(request):
    """Require Admin or DEO role"""
    
def can_write(user):
    """Check if user can write data"""
    return user['role'] in ('Admin', 'DEO')
    
def can_send_notifications(user):
    """Check if user can send notifications"""
    return user['role'] in ('Admin', 'DEO', 'HOD')
    
def can_manage_users(user):
    """Check if user can manage other users"""
    return user['role'] == 'Admin'
```

### Role Hierarchy

```
Admin (Highest)
  ├─ Full system access
  ├─ User management
  └─ All features

DEO
  ├─ Full data access
  ├─ Email notifications
  └─ Most features

HOD
  ├─ View all data
  ├─ Email notifications
  └─ Reports only

Faculty/Student/Others (Lowest)
  ├─ View limited data
  └─ Basic features only
```

---

**Last Updated**: April 9, 2026
**Version**: 1.0
**Status**: Production Ready ✅
