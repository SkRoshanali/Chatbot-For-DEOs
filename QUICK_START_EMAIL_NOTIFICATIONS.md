# Quick Start: Email Notifications & Session Timeout

## 🚀 5-Minute Setup Guide

### Step 1: Configure Email Passwords (2 minutes)

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Generate App Passwords** for each Gmail account:
   
   **For DEO (231fa04436@gmail.com):**
   - Visit: https://myaccount.google.com/security
   - Enable "2-Step Verification" if not already enabled
   - Scroll to "App passwords"
   - Select app: "Mail"
   - Select device: "Other" → Type "Smart DEO"
   - Click "Generate"
   - Copy the 16-character password (ignore spaces)
   
   **Repeat for HOD (231fa04476@gmail.com) and Admin (231fa04446@gmail.com)**

3. **Add passwords to `.env` file:**
   ```bash
   # Open .env file and add:
   DEO_EMAIL_PASSWORD=abcdefghijklmnop
   HOD_EMAIL_PASSWORD=qrstuvwxyzabcdef
   ADMIN_EMAIL_PASSWORD=ghijklmnopqrstuv
   ```

### Step 2: Test Email Configuration (1 minute)

```bash
python test_email_setup.py
```

**Expected Output:**
```
============================================================
  Smart DEO Email Configuration Test
============================================================

============================================================
  Configuration Check
============================================================

Testing DEO configuration...
  Email: 231fa04436@gmail.com
  Name: DEO - Smart DEO System
  ✅ Password configured (length: 16)

Testing HOD configuration...
  Email: 231fa04476@gmail.com
  Name: HOD - Smart DEO System
  ✅ Password configured (length: 16)

Testing Admin configuration...
  Email: 231fa04446@gmail.com
  Name: Admin - Smart DEO System
  ✅ Password configured (length: 16)

============================================================
  Configuration Summary
============================================================

  ✅ DEO: Configured
  ✅ HOD: Configured
  ✅ Admin: Configured

  3/3 roles configured

Do you want to send test emails? (y/n):
```

**Send test email:**
- Type `y` and press Enter
- Enter your email address
- Check your inbox for 3 test emails (one from each role)

### Step 3: Start Application (1 minute)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Use Email Notifications (1 minute)

1. **Open browser:** http://localhost:8000
2. **Login** with your credentials
3. **Navigate to Console** → Click "Email Notifications"
4. **Send notification:**
   - Select type: "Low Attendance Alert"
   - Enter recipient email
   - Select students from list
   - Click "Send Notifications"

---

## 📧 Email Features

### What You Can Do

✅ **Send Low Attendance Alerts**
- Automatically finds students with attendance < 75%
- Sends detailed alert to faculty
- Includes student info and action required

✅ **Send Poor Performance Alerts**
- Finds students with CGPA < 6.0
- Alerts faculty for intervention
- Includes academic details and backlogs

✅ **Send Weekly Reports**
- Comprehensive department statistics
- Overall metrics and at-risk counts
- Perfect for HOD/Admin monitoring

### Role-Based Sending

- **DEO** sends from: 231fa04436@gmail.com
- **HOD** sends from: 231fa04476@gmail.com
- **Admin** sends from: 231fa04446@gmail.com

System automatically uses the correct sender based on who's logged in!

---

## ⏱️ Session Timeout

### How It Works

- **15-minute timeout** (configurable)
- **Visual timer** in sidebar footer
- **Auto-logout** when expired
- **Activity tracking** resets timer

### Timer Colors

- 🟢 **Green/Pink** (> 5 minutes): Normal
- 🟡 **Yellow** (2-5 minutes): Warning
- 🔴 **Red** (< 2 minutes): Critical

### Adjusting Timeout

**Quick change in `.env`:**
```bash
SESSION_TIMEOUT=20  # 20 minutes
```

**Or in `main.py`:**
```python
app.add_middleware(
    SessionMiddleware,
    max_age=1200  # 1200 seconds = 20 minutes
)
```

---

## 🐛 Troubleshooting

### Email Not Sending?

**Check 1:** App Password correct?
```bash
python test_email_setup.py
```

**Check 2:** 2-Step Verification enabled?
- Go to https://myaccount.google.com/security
- Verify "2-Step Verification" is ON

**Check 3:** Check console logs
```bash
# Look for:
[Email] Sent to faculty@example.com: ⚠️ Low Attendance Alert
# Or:
[Email] Authentication failed for DEO
```

**Check 4:** Firewall blocking SMTP?
- Port 587 must be open
- Try from different network

### Session Timer Not Working?

**Check 1:** Hard refresh browser
```
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

**Check 2:** Check browser console
```
F12 → Console tab
Look for JavaScript errors
```

**Check 3:** Verify timer element exists
```javascript
// In browser console:
document.getElementById('sessionTimer')
// Should return: <div id="sessionTimer">...</div>
```

---

## 📊 Usage Examples

### Example 1: Send Low Attendance Alert

1. Login as DEO
2. Go to Notifications page
3. Select "Low Attendance Alert"
4. Enter: `faculty@example.com`
5. Check students with low attendance
6. Click "Send Notifications"
7. ✅ Email sent from 231fa04436@gmail.com

### Example 2: Send Weekly Report

1. Login as HOD
2. Go to Notifications page
3. Scroll to "Weekly Performance Report"
4. Enter: `hod@example.com`
5. Click "Send Report"
6. ✅ Comprehensive report sent from 231fa04476@gmail.com

### Example 3: Monitor Session

1. Login to system
2. Check sidebar footer: `⏱ 15:00`
3. Work normally (timer resets on activity)
4. If idle, timer counts down
5. At `⏱ 01:30`, timer turns red
6. At `⏱ 00:00`, auto-logout

---

## 🎯 Best Practices

### Email Notifications

1. **Verify recipients** before sending
2. **Select appropriate students** (don't spam)
3. **Use correct notification type**
4. **Monitor success/failure counts**
5. **Check recipient inbox** (including spam)

### Session Management

1. **Watch the timer** when working
2. **Save work frequently**
3. **Logout when done** (don't rely on timeout)
4. **Lock computer** when away
5. **Use appropriate timeout** for your environment

---

## 📚 Additional Resources

- **Full Guide:** `EMAIL_NOTIFICATIONS_GUIDE.md`
- **Implementation Details:** `EMAIL_AND_TIMEOUT_IMPLEMENTATION_SUMMARY.md`
- **Test Script:** `test_email_setup.py`

---

## ✅ Quick Checklist

Before going live:

- [ ] Email passwords configured in `.env`
- [ ] Test script runs successfully
- [ ] Test emails received in inbox
- [ ] Application starts without errors
- [ ] Can login and access notifications page
- [ ] Can send test notification
- [ ] Session timer displays correctly
- [ ] Session timeout works (test by waiting)
- [ ] All roles can send emails (DEO, HOD, Admin)

---

## 🆘 Need Help?

1. **Check logs:** Console output shows detailed errors
2. **Run test:** `python test_email_setup.py`
3. **Verify config:** Check `.env` file has correct passwords
4. **Test manually:** Try sending email from Gmail web interface
5. **Check network:** Ensure port 587 is accessible

---

**Setup Time:** ~5 minutes
**Status:** ✅ Production Ready
**Last Updated:** April 2026
