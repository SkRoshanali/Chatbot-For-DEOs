# Email Notification System - Complete Guide

## Overview
The Smart DEO application includes a real-time email notification system with role-based senders. Each role (DEO, HOD, Admin) sends emails from their designated email address.

## Role-Based Email Addresses

| Role  | Email Address         | Environment Variable      |
|-------|-----------------------|---------------------------|
| DEO   | 231fa04436@gmail.com  | DEO_EMAIL_PASSWORD        |
| HOD   | 231fa04476@gmail.com  | HOD_EMAIL_PASSWORD        |
| Admin | 231fa04446@gmail.com  | ADMIN_EMAIL_PASSWORD      |

## Setup Instructions

### Step 1: Enable Gmail App Passwords

For each email account (DEO, HOD, Admin):

1. Go to your Google Account: https://myaccount.google.com/
2. Select **Security** from the left menu
3. Under "Signing in to Google", select **2-Step Verification** (enable if not already)
4. Scroll down and select **App passwords**
5. Select app: **Mail**
6. Select device: **Other (Custom name)** → Enter "Smart DEO"
7. Click **Generate**
8. Copy the 16-character password (remove spaces)

### Step 2: Configure Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Email Configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Role-based Email Credentials
# DEO Email: 231fa04436@gmail.com
DEO_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx

# HOD Email: 231fa04476@gmail.com
HOD_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx

# Admin Email: 231fa04446@gmail.com
ADMIN_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
```

**Important:** Replace `xxxx xxxx xxxx xxxx` with the actual App Passwords generated in Step 1.

### Step 3: Test Email Configuration

Run the email service test:

```bash
python email_service.py
```

This will check if all role-based email credentials are configured correctly.

## Features

### 1. Individual Student Notifications

Send targeted alerts for specific students:

- **Low Attendance Alert**: For students with attendance < 75%
- **Poor Performance Alert**: For students with CGPA < 6.0

**How to use:**
1. Navigate to `/notifications` page
2. Select notification type
3. Choose students from the list
4. Enter recipient email (faculty/parent)
5. Click "Send Notifications"

### 2. Bulk Performance Reports

Send weekly/monthly performance summaries:

- Total students count
- Average CGPA and attendance
- At-risk students count
- Students with backlogs

**How to use:**
1. Navigate to `/notifications` page
2. Scroll to "Weekly Performance Report" section
3. Enter recipient email (HOD/Principal)
4. Click "Send Report"

### 3. Real-Time Sending

- Emails are sent immediately when triggered
- No queue or delay
- Instant feedback on success/failure
- Error messages displayed for troubleshooting

## Email Templates

### Low Attendance Alert
```
Subject: ⚠️ Low Attendance Alert - [Student Name]

Content:
- Student details (Name, Roll, Section)
- Current attendance percentage (highlighted in red)
- CGPA
- Action required message
- Timestamp
```

### Poor Performance Alert
```
Subject: 📉 Performance Alert - [Student Name]

Content:
- Student details (Name, Roll, Section)
- CGPA (highlighted in red)
- Backlogs count
- Action required message
- Timestamp
```

### Weekly Performance Report
```
Subject: 📊 Weekly Performance Report - [Date]

Content:
- Overall statistics (Total students, Avg CGPA, Avg Attendance)
- Alert counts (Low attendance, At-risk, With backlogs)
- Timestamp
```

## Session Timeout Configuration

### Current Settings
- **Default Timeout**: 15 minutes of inactivity
- **Countdown Timer**: Visible in sidebar
- **Auto-logout**: Session expires after timeout

### How It Works

1. **Session Start**: Timer starts when user logs in
2. **Activity Tracking**: Updates on user interactions (not API calls)
3. **Warning**: Visual countdown in sidebar shows remaining time
4. **Expiration**: Automatic logout and redirect to login page

### Configuring Timeout

Edit `.env` file:

```bash
# Session Timeout (in minutes)
SESSION_TIMEOUT=15
```

Change `15` to your desired timeout (in minutes):
- **5 minutes**: High security, frequent re-authentication
- **15 minutes**: Balanced (recommended)
- **30 minutes**: Longer sessions, less interruption
- **60 minutes**: Maximum convenience

### Timeout Best Practices

**For DEO/Admin (Data Entry):**
- Recommended: 30-60 minutes
- Reason: Frequent data entry tasks need longer sessions

**For HOD (Viewing Reports):**
- Recommended: 15-30 minutes
- Reason: Balanced security and convenience

**For Public/Shared Computers:**
- Recommended: 5-10 minutes
- Reason: Enhanced security on shared devices

## Troubleshooting

### Issue: "SMTP Authentication Failed"

**Solution:**
1. Verify App Password is correct (16 characters, no spaces)
2. Ensure 2-Step Verification is enabled on Gmail account
3. Check if "Less secure app access" is NOT enabled (use App Passwords instead)
4. Regenerate App Password if needed

### Issue: "SMTP Connection Timeout"

**Solution:**
1. Check internet connection
2. Verify SMTP_HOST=smtp.gmail.com and SMTP_PORT=587
3. Check firewall settings (allow port 587)
4. Try alternative port: 465 (SSL) instead of 587 (TLS)

### Issue: "Recipient Email Not Receiving"

**Solution:**
1. Check recipient's spam/junk folder
2. Verify recipient email address is correct
3. Check Gmail sending limits (500 emails/day for free accounts)
4. Wait a few minutes and try again

### Issue: "Session Expires Too Quickly"

**Solution:**
1. Increase SESSION_TIMEOUT in `.env` file
2. Restart the application
3. Clear browser cache and cookies
4. Check system clock is synchronized

### Issue: "Session Timer Not Updating"

**Solution:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Check JavaScript console for errors
4. Verify `static/script.js` is loaded correctly

## Security Recommendations

### Email Security
1. **Never commit** `.env` file to version control
2. **Rotate passwords** every 3-6 months
3. **Use App Passwords** only (never regular passwords)
4. **Monitor** Gmail account activity regularly
5. **Revoke** unused App Passwords

### Session Security
1. **Use HTTPS** in production
2. **Set appropriate timeout** based on environment
3. **Clear sessions** on logout
4. **Implement CSRF protection** (already included)
5. **Monitor** active sessions

## Testing Checklist

Before deploying to production:

- [ ] All three role email accounts configured
- [ ] App Passwords generated and added to `.env`
- [ ] Test email sent successfully from each role
- [ ] Low attendance alert received
- [ ] Poor performance alert received
- [ ] Bulk report received
- [ ] Session timeout working correctly
- [ ] Timer countdown visible in sidebar
- [ ] Auto-logout on timeout working
- [ ] Email templates display correctly
- [ ] Error messages clear and helpful

## API Endpoints

### Send Individual Notifications
```
POST /api/notifications/send
Body: {
  "type": "low_attendance" | "poor_performance",
  "email": "recipient@example.com",
  "students": ["231FA00001", "231FA00002"]
}
```

### Send Bulk Report
```
POST /api/notifications/bulk-report
Body: {
  "email": "recipient@example.com"
}
```

### Get At-Risk Students
```
GET /api/notifications/at-risk
Response: {
  "success": true,
  "low_attendance": [...],
  "poor_performance": [...],
  "with_backlogs": [...]
}
```

## Performance Considerations

### Email Sending
- **Synchronous**: Emails sent immediately (blocks request)
- **Timeout**: 30 seconds per email
- **Batch Limit**: Recommend max 50 students per batch
- **Rate Limit**: Gmail allows 500 emails/day

### Session Management
- **Storage**: Server-side sessions (secure)
- **Cleanup**: Automatic on timeout
- **Memory**: Minimal overhead per session
- **Scalability**: Supports 100+ concurrent users

## Future Enhancements

### Planned Features
1. **Async Email Queue**: Background job processing
2. **Email Templates**: Customizable templates
3. **Scheduled Reports**: Daily/weekly automated reports
4. **SMS Notifications**: Integration with SMS gateway
5. **Push Notifications**: Browser push notifications
6. **Email Analytics**: Track open rates and clicks
7. **Bulk Actions**: Send to entire section/department
8. **Custom Timeout**: Per-role timeout settings

## Support

For issues or questions:
1. Check this guide first
2. Review error messages in console
3. Test email configuration with `python email_service.py`
4. Check Gmail account activity logs
5. Verify environment variables are set correctly

## Quick Reference

### Environment Variables
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
DEO_EMAIL_PASSWORD=your_app_password
HOD_EMAIL_PASSWORD=your_app_password
ADMIN_EMAIL_PASSWORD=your_app_password
SESSION_TIMEOUT=15
```

### Gmail App Password URL
https://myaccount.google.com/apppasswords

### Test Command
```bash
python email_service.py
```

### Restart Application
```bash
# Stop current process (Ctrl+C)
# Then restart:
python main.py
# or
uvicorn main:app --reload
```
