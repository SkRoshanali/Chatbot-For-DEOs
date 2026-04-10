# Email Notifications & Session Timeout Guide

## Overview
The Smart DEO system now supports real-time email notifications with role-based sender emails and automatic session timeout for security.

---

## Email Notification Features

### Role-Based Sender Emails
Each role has its own dedicated email address for sending notifications:

| Role  | Email Address          | Purpose                           |
|-------|------------------------|-----------------------------------|
| DEO   | 231fa04436@gmail.com   | Department-level notifications    |
| HOD   | 231fa04476@gmail.com   | Head of Department communications |
| Admin | 231fa04446@gmail.com   | Administrative notifications      |

### Notification Types

1. **Low Attendance Alert**
   - Triggered for students with attendance < 75%
   - Includes student details, current attendance, and CGPA
   - Sent to faculty/HOD for follow-up action

2. **Poor Performance Alert**
   - Triggered for students with CGPA < 6.0
   - Includes academic details and backlog information
   - Sent to faculty/counselors for intervention

3. **Weekly Performance Report**
   - Comprehensive department statistics
   - Includes overall metrics and at-risk student counts
   - Sent to HOD/Admin for monitoring

---

## Email Configuration Setup

### Step 1: Enable Gmail App Passwords

For each role email (DEO, HOD, Admin):

1. Go to Google Account settings: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (enable if not already)
3. Scroll down to **App passwords**
4. Click **Select app** → Choose "Mail"
5. Click **Select device** → Choose "Other" → Enter "Smart DEO System"
6. Click **Generate**
7. Copy the 16-character password (remove spaces)

### Step 2: Configure Environment Variables

Create a `.env` file in your project root (copy from `.env.example`):

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Role-based Email Credentials
DEO_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
HOD_EMAIL_PASSWORD=yyyy yyyy yyyy yyyy
ADMIN_EMAIL_PASSWORD=zzzz zzzz zzzz zzzz
```

**Important:** Replace the placeholder passwords with actual App Passwords generated in Step 1.

### Step 3: Test Email Configuration

Run the email service test:

```bash
python email_service.py
```

Expected output:
```
Testing email configuration for all roles:

[Email] Configuration for DEO:
  Host: smtp.gmail.com:587
  User: 231fa04436@gmail.com
  From: DEO - Smart DEO System <231fa04436@gmail.com>

[Email] Configuration for HOD:
  Host: smtp.gmail.com:587
  User: 231fa04476@gmail.com
  From: HOD - Smart DEO System <231fa04476@gmail.com>

[Email] Configuration for Admin:
  Host: smtp.gmail.com:587
  User: 231fa04446@gmail.com
  From: Admin - Smart DEO System <231fa04446@gmail.com>
```

---

## Using Email Notifications

### Access the Notifications Page

1. Log in to Smart DEO system
2. Navigate to **Console** → Click **Email Notifications** card
3. Or directly visit: `http://localhost:8000/notifications`

### Send Individual Notifications

1. **Select Notification Type:**
   - Low Attendance Alert
   - Poor Performance Alert

2. **Enter Recipient Email:**
   - Faculty email address
   - HOD email address
   - Any valid email

3. **Select Students:**
   - System automatically loads at-risk students
   - Check boxes next to students you want to notify about
   - Multiple students can be selected

4. **Click "Send Notifications"**
   - System sends emails in real-time
   - Shows success/failure count
   - Displays any errors

### Send Bulk Reports

1. **Enter Recipient Email** (typically HOD or Admin)
2. **Click "Send Report"**
3. Report includes:
   - Total students
   - Average CGPA and attendance
   - Low attendance count
   - At-risk students count
   - Students with backlogs

---

## Session Timeout Feature

### How It Works

- **Timeout Duration:** 15 minutes (configurable)
- **Auto-logout:** User is logged out after 15 minutes of inactivity
- **Visual Timer:** Countdown timer displayed in sidebar
- **Warning:** Timer turns red when < 2 minutes remaining

### Session Timer Display

Located in the sidebar footer:
```
⏱ 14:32  ← Green (safe)
⏱ 01:45  ← Yellow (warning)
⏱ 00:30  ← Red (critical)
```

### Activity Tracking

Session is refreshed on:
- Page navigation (chat, console, data management)
- Form submissions
- Report generation
- Any user interaction

Session is NOT refreshed on:
- Background API calls
- Auto-refresh timers
- Keepalive pings

### Configuring Timeout

Edit `.env` file:
```bash
# Session timeout in minutes (default: 15)
SESSION_TIMEOUT=15
```

Or modify in `main.py`:
```python
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.environ.get('SECRET_KEY', 'deo_chatbot_secret_key_2024'),
    max_age=900  # 900 seconds = 15 minutes
)
```

---

## Troubleshooting

### Email Not Sending

**Problem:** Emails fail to send

**Solutions:**
1. Check App Password is correct (no spaces)
2. Verify 2-Step Verification is enabled on Gmail
3. Check SMTP settings (host: smtp.gmail.com, port: 587)
4. Review console logs for specific error messages
5. Test with: `python email_service.py`

**Common Errors:**
```
[Email] Authentication failed for DEO
→ Solution: Regenerate App Password

[Email] SMTP credentials not configured for role: DEO
→ Solution: Set DEO_EMAIL_PASSWORD in .env file

[Email] SMTP error: Connection refused
→ Solution: Check firewall/network settings
```

### Session Timeout Issues

**Problem:** Session expires too quickly

**Solution:** Increase `SESSION_TIMEOUT` in `.env` or `max_age` in middleware

**Problem:** Timer not updating

**Solution:** Hard refresh browser (Ctrl+Shift+R) to clear cached JavaScript

**Problem:** Logged out unexpectedly

**Solution:** Check if session timeout is too short, or if there's a server restart

---

## Best Practices

### Email Notifications

1. **Use Appropriate Sender Role:**
   - DEO for routine student alerts
   - HOD for department-wide reports
   - Admin for system-wide communications

2. **Batch Notifications:**
   - Select multiple students at once
   - Reduces API calls and improves performance

3. **Verify Recipients:**
   - Double-check email addresses before sending
   - Use institutional email addresses

4. **Monitor Delivery:**
   - Check success/failure counts
   - Review error messages for failed sends

### Session Security

1. **Always Logout:**
   - Click logout button when done
   - Don't rely solely on timeout

2. **Monitor Timer:**
   - Keep eye on session timer
   - Refresh session before it expires

3. **Secure Workstation:**
   - Lock computer when away
   - Don't leave browser open unattended

4. **Regular Password Changes:**
   - Update App Passwords periodically
   - Rotate credentials every 90 days

---

## API Endpoints

### Send Individual Notifications
```http
POST /api/notifications/send
Content-Type: application/json

{
  "type": "low_attendance",
  "email": "faculty@example.com",
  "students": ["CSE001", "CSE002"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sent 2 notifications",
  "sent": 2,
  "failed": 0,
  "errors": null
}
```

### Send Bulk Report
```http
POST /api/notifications/bulk-report
Content-Type: application/json

{
  "email": "hod@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Report sent successfully"
}
```

### Get At-Risk Students
```http
GET /api/notifications/at-risk
```

**Response:**
```json
{
  "success": true,
  "low_attendance": [...],
  "poor_performance": [...],
  "with_backlogs": [...]
}
```

---

## Security Considerations

1. **Email Credentials:**
   - Never commit `.env` file to version control
   - Use App Passwords, not account passwords
   - Rotate passwords regularly

2. **Session Management:**
   - Sessions stored server-side
   - Encrypted with SECRET_KEY
   - Auto-expire after timeout

3. **Access Control:**
   - Only DEO and Admin can send notifications
   - Role-based email sending
   - Audit logs for all email sends

4. **Data Privacy:**
   - Student data encrypted in transit
   - Email content sanitized
   - No sensitive data in logs

---

## Support

For issues or questions:
1. Check console logs for error messages
2. Review this guide for troubleshooting steps
3. Test email configuration with `python email_service.py`
4. Verify environment variables are set correctly

---

**Last Updated:** April 2026
**Version:** 2.0
