# Administrator Setup Checklist

## Pre-Deployment Checklist

Use this checklist to ensure the Smart DEO application is properly configured before deployment.

---

## ✅ Database Configuration

- [ ] MySQL server installed and running
- [ ] Database `deo_chatbot` created
- [ ] Database user has proper permissions
- [ ] Connection tested successfully
- [ ] `.env` file has correct database credentials:
  ```bash
  MYSQL_HOST=localhost
  MYSQL_PORT=3306
  MYSQL_USER=root
  MYSQL_PASSWORD=your_password
  MYSQL_DATABASE=deo_chatbot
  ```

**Test Command**:
```bash
mysql -u root -p -e "SHOW DATABASES LIKE 'deo_chatbot';"
```

---

## ✅ Email Configuration

### Gmail Accounts Setup

- [ ] DEO Gmail account (231fa04436@gmail.com) accessible
- [ ] HOD Gmail account (231fa04476@gmail.com) accessible
- [ ] Admin Gmail account (231fa04446@gmail.com) accessible
- [ ] 2-Step Verification enabled on all accounts
- [ ] App Passwords generated for all accounts

### App Password Generation

For each account (DEO, HOD, Admin):

1. [ ] Visit https://myaccount.google.com/apppasswords
2. [ ] Select App: Mail
3. [ ] Select Device: Other (Custom name) → "Smart DEO"
4. [ ] Click Generate
5. [ ] Copy 16-character password
6. [ ] Save password securely

### Environment Configuration

- [ ] `.env` file created (copied from `.env.example`)
- [ ] DEO_EMAIL_PASSWORD added to `.env`
- [ ] HOD_EMAIL_PASSWORD added to `.env`
- [ ] ADMIN_EMAIL_PASSWORD added to `.env`
- [ ] SMTP_HOST set to smtp.gmail.com
- [ ] SMTP_PORT set to 587

**Example `.env` section**:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
DEO_EMAIL_PASSWORD=abcd efgh ijkl mnop
HOD_EMAIL_PASSWORD=abcd efgh ijkl mnop
ADMIN_EMAIL_PASSWORD=abcd efgh ijkl mnop
```

### Email Testing

- [ ] Setup wizard run: `python setup_email_notifications.py`
- [ ] Test email sent from DEO account
- [ ] Test email sent from HOD account
- [ ] Test email sent from Admin account
- [ ] All test emails received successfully
- [ ] Emails not in spam folder

---

## ✅ Session Timeout Configuration

- [ ] SESSION_TIMEOUT set in `.env` file
- [ ] Timeout value appropriate for environment:
  - [ ] Production: 15 minutes (recommended)
  - [ ] Development: 60 minutes
  - [ ] High Security: 5-10 minutes
- [ ] Timeout tested and working
- [ ] Timer visible in sidebar
- [ ] Auto-logout working correctly

**Example `.env` section**:
```bash
SESSION_TIMEOUT=15
```

---

## ✅ Security Configuration

- [ ] SECRET_KEY set to strong random value
- [ ] MASTER_PASSWORD changed from default
- [ ] MASTER_OTP configured (or left as 000000 for testing)
- [ ] `.env` file NOT committed to version control
- [ ] `.gitignore` includes `.env`
- [ ] File permissions set correctly (600 for `.env`)

**Generate Strong SECRET_KEY**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example `.env` section**:
```bash
SECRET_KEY=your_generated_secret_key_here
MASTER_PASSWORD=YourStrongPassword123!
MASTER_OTP=000000
```

---

## ✅ User Accounts

### Default Users Created

- [ ] Admin account created
- [ ] DEO account created
- [ ] HOD account created
- [ ] QR codes generated for all users
- [ ] OTP secrets saved securely

### User Testing

- [ ] Admin can login successfully
- [ ] DEO can login successfully
- [ ] HOD can login successfully
- [ ] OTP authentication working
- [ ] Role-based access working correctly

---

## ✅ Application Dependencies

- [ ] Python 3.8+ installed
- [ ] All requirements installed: `pip install -r requirements.txt`
- [ ] MySQL connector installed
- [ ] FastAPI installed
- [ ] All dependencies up to date

**Install Command**:
```bash
pip install -r requirements.txt
```

---

## ✅ Application Startup

- [ ] Application starts without errors
- [ ] Database connection successful
- [ ] All routes accessible
- [ ] Static files loading correctly
- [ ] No error messages in console

**Start Command**:
```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## ✅ Feature Testing

### Console Page

- [ ] Console page accessible at `/console`
- [ ] All feature cards visible
- [ ] Statistics loading correctly
- [ ] Role-based features showing correctly
- [ ] Navigation links working

### Chat/Chatbot

- [ ] Chat page accessible at `/chat`
- [ ] Bot responds to queries
- [ ] Quick report buttons working
- [ ] Export functionality working
- [ ] Filters working correctly

### Data Management

- [ ] Data page accessible at `/data` (DEO/Admin only)
- [ ] Manual entry form working
- [ ] File upload working
- [ ] View data table working
- [ ] Edit/delete functions working

### Dashboard

- [ ] Dashboard accessible at `/dashboard`
- [ ] Charts loading correctly
- [ ] Statistics accurate
- [ ] Data refreshing properly
- [ ] Responsive on mobile

### Email Notifications

- [ ] Notifications page accessible at `/notifications` (DEO/Admin only)
- [ ] At-risk students loading
- [ ] Individual notifications sending
- [ ] Bulk reports sending
- [ ] Error handling working

---

## ✅ Navigation Testing

- [ ] Console link visible on all pages
- [ ] All navigation links working
- [ ] Breadcrumbs correct
- [ ] Back buttons working
- [ ] Logout working correctly

---

## ✅ Session Management

- [ ] Login working correctly
- [ ] Session persists across pages
- [ ] Session timeout working
- [ ] Timer countdown visible
- [ ] Auto-logout on timeout
- [ ] Manual logout working

---

## ✅ Data Validation

### Sample Data

- [ ] Sample students loaded
- [ ] Sample users created
- [ ] Subject marks populated
- [ ] All fields have valid data
- [ ] No null/missing critical data

### Data Integrity

- [ ] Roll numbers unique
- [ ] CGPA values valid (0-10)
- [ ] Attendance values valid (0-100)
- [ ] Marks values valid (internal: 0-50, external: 0-100)
- [ ] Foreign keys working

---

## ✅ Performance Testing

- [ ] Page load times acceptable (<3 seconds)
- [ ] Database queries optimized
- [ ] Indexes created on key columns
- [ ] No memory leaks
- [ ] Concurrent users supported (test with 10+ users)

---

## ✅ Error Handling

- [ ] 404 pages handled gracefully
- [ ] 401 unauthorized handled
- [ ] 403 forbidden handled
- [ ] 500 server errors logged
- [ ] User-friendly error messages

---

## ✅ Mobile Responsiveness

- [ ] Console page responsive
- [ ] Chat page responsive
- [ ] Data page responsive
- [ ] Dashboard responsive
- [ ] Notifications page responsive
- [ ] Forms usable on mobile
- [ ] Tables scrollable on mobile

---

## ✅ Browser Compatibility

- [ ] Chrome/Edge working
- [ ] Firefox working
- [ ] Safari working (if applicable)
- [ ] Mobile browsers working
- [ ] No console errors

---

## ✅ Documentation

- [ ] README.md updated
- [ ] HOW_TO_START.md reviewed
- [ ] EMAIL_NOTIFICATION_GUIDE.md available
- [ ] SESSION_TIMEOUT_GUIDE.md available
- [ ] NOTIFICATION_PAGE_USAGE.md available
- [ ] All guides accessible to users

---

## ✅ Backup and Recovery

- [ ] Database backup procedure documented
- [ ] `.env` file backed up securely
- [ ] Recovery procedure tested
- [ ] Backup schedule established
- [ ] Backup location secured

**Backup Command**:
```bash
mysqldump -u root -p deo_chatbot > backup_$(date +%Y%m%d).sql
```

---

## ✅ Monitoring and Logging

- [ ] Application logs configured
- [ ] Error logs monitored
- [ ] Email sending logged
- [ ] Session activity logged
- [ ] Database queries logged (if needed)

---

## ✅ Production Deployment

### Pre-Deployment

- [ ] All checklist items above completed
- [ ] Production `.env` configured
- [ ] Production database ready
- [ ] SSL certificate installed (HTTPS)
- [ ] Domain name configured
- [ ] Firewall rules set

### Deployment

- [ ] Application deployed to production server
- [ ] Database migrated to production
- [ ] `.env` file copied to production
- [ ] Dependencies installed on production
- [ ] Application started successfully
- [ ] Health check passing

### Post-Deployment

- [ ] Production URL accessible
- [ ] All features working in production
- [ ] Email sending working in production
- [ ] Session timeout working in production
- [ ] No errors in production logs
- [ ] Users can login successfully

---

## ✅ User Training

- [ ] Admin trained on all features
- [ ] DEO trained on data management
- [ ] HOD trained on viewing reports
- [ ] Email notification usage explained
- [ ] Troubleshooting guide provided
- [ ] Support contact information shared

---

## ✅ Maintenance Plan

- [ ] Update schedule established
- [ ] Backup schedule established
- [ ] Monitoring schedule established
- [ ] Password rotation schedule established
- [ ] Database maintenance scheduled
- [ ] Support process documented

---

## Quick Reference Commands

### Start Application
```bash
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Test Email Configuration
```bash
python setup_email_notifications.py
```

### Test Email Service Directly
```bash
python email_service.py
```

### Database Backup
```bash
mysqldump -u root -p deo_chatbot > backup.sql
```

### Database Restore
```bash
mysql -u root -p deo_chatbot < backup.sql
```

### Check Application Status
```bash
curl http://localhost:8000/api/dbstatus
```

### View Logs
```bash
tail -f application.log
```

---

## Support Contacts

**Technical Issues**:
- Email: support@example.com
- Phone: +91-XXXXXXXXXX

**Email Configuration**:
- Gmail Support: https://support.google.com/mail
- App Passwords: https://myaccount.google.com/apppasswords

**Documentation**:
- Email Guide: `EMAIL_NOTIFICATION_GUIDE.md`
- Timeout Guide: `SESSION_TIMEOUT_GUIDE.md`
- Usage Guide: `NOTIFICATION_PAGE_USAGE.md`
- Setup Summary: `EMAIL_AND_TIMEOUT_IMPLEMENTATION_SUMMARY.md`

---

## Completion Sign-Off

**Deployment Date**: _______________

**Deployed By**: _______________

**Verified By**: _______________

**Production URL**: _______________

**Notes**:
_______________________________________________________
_______________________________________________________
_______________________________________________________

---

**Status**: 
- [ ] Ready for Production
- [ ] Needs Additional Testing
- [ ] Issues Found (document below)

**Issues/Notes**:
_______________________________________________________
_______________________________________________________
_______________________________________________________

---

**Last Updated**: April 9, 2026
**Version**: 1.0
