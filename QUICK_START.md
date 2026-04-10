# 🚀 Quick Start - Email Notifications & Session Timeout

## 3-Minute Setup Guide

### Step 1: Get Gmail App Passwords (5 minutes)

For each email account:

1. **DEO** (231fa04436@gmail.com)
2. **HOD** (231fa04476@gmail.com)
3. **Admin** (231fa04446@gmail.com)

**Do this:**
```
1. Go to: https://myaccount.google.com/apppasswords
2. Enable 2-Step Verification (if not already)
3. Click "App passwords"
4. Select: Mail → Other (Custom name) → "Smart DEO"
5. Click Generate
6. Copy the 16-character password (remove spaces)
```

### Step 2: Configure Environment (1 minute)

```bash
# Copy example file
cp .env.example .env

# Edit .env and add your App Passwords
nano .env  # or use any text editor
```

Add these lines:
```bash
DEO_EMAIL_PASSWORD=your_16_char_password
HOD_EMAIL_PASSWORD=your_16_char_password
ADMIN_EMAIL_PASSWORD=your_16_char_password
SESSION_TIMEOUT=15
```

### Step 3: Test Configuration (1 minute)

```bash
python setup_email_notifications.py
```

Follow the prompts:
- Enter your email for testing
- Check your inbox
- Verify all 3 test emails received

### Step 4: Start Application (30 seconds)

```bash
python main.py
```

Or:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Test in Browser (1 minute)

1. Open: `http://localhost:8000`
2. Login (username: `admin`, password: `admin123`)
3. Navigate to `/notifications`
4. Send a test email to yourself
5. Check timer in sidebar (⏱ 15:00)

---

## ✅ Done!

Your email notifications are now working with:
- ✅ Role-based senders (DEO, HOD, Admin)
- ✅ Real-time sending
- ✅ Session timeout (15 minutes)
- ✅ Visual countdown timer

---

## Common Issues

### "SMTP Authentication Failed"
**Fix**: Check App Password is correct (16 characters, no spaces)

### "Emails not received"
**Fix**: Check spam folder, wait 5 minutes

### "Session expires too quickly"
**Fix**: Increase `SESSION_TIMEOUT` in `.env`, restart app

---

## Need Help?

**Setup Wizard**:
```bash
python setup_email_notifications.py
```

**Documentation**:
- Complete Guide: `EMAIL_NOTIFICATION_GUIDE.md`
- Timeout Guide: `SESSION_TIMEOUT_GUIDE.md`
- User Guide: `NOTIFICATION_PAGE_USAGE.md`
- Admin Checklist: `ADMIN_SETUP_CHECKLIST.md`

**Test Email Service**:
```bash
python email_service.py
```

---

## Quick Reference

| Feature | URL | Access |
|---------|-----|--------|
| Console | `/console` | All |
| Chat | `/chat` | All |
| Notifications | `/notifications` | DEO, Admin |
| Data Management | `/data` | DEO, Admin |
| Dashboard | `/dashboard` | All |

| Email | Role | Password Variable |
|-------|------|-------------------|
| 231fa04436@gmail.com | DEO | DEO_EMAIL_PASSWORD |
| 231fa04476@gmail.com | HOD | HOD_EMAIL_PASSWORD |
| 231fa04446@gmail.com | Admin | ADMIN_EMAIL_PASSWORD |

| Timeout | Use Case |
|---------|----------|
| 5 min | High security |
| 15 min | Standard (default) |
| 30 min | Convenience |
| 60 min | Development |

---

**That's it! You're ready to go! 🎉**
