# Email Notifications Page - User Guide

## Accessing the Notifications Page

**URL**: `/notifications`

**Who can access**: DEO and Admin roles only

**Navigation**:
1. Login to Smart DEO
2. Click "Console" from any page
3. Click "Email Notifications" card
4. Or directly navigate to: `http://your-server:8000/notifications`

## Page Overview

The notifications page has 4 main sections:

```
┌─────────────────────────────────────────────────────────┐
│  📧 Email Notifications                    [Navigation]  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  1. At-Risk Students Overview                            │
│     ┌──────────┬──────────────┬──────────────┐          │
│     │ Low Att  │ Poor Perf    │ Backlogs     │          │
│     │   12     │      8       │      5       │          │
│     └──────────┴──────────────┴──────────────┘          │
│                                                           │
│  2. Send Individual Notifications                        │
│     [Notification Type ▼] [Recipient Email]              │
│     [✓] Student 1 - Att: 65%                            │
│     [✓] Student 2 - Att: 70%                            │
│     [ ] Student 3 - Att: 72%                            │
│     [Send Notifications]                                 │
│                                                           │
│  3. Send Weekly Performance Report                       │
│     [Recipient Email]                                    │
│     [Send Report]                                        │
│                                                           │
│  4. Configuration                                        │
│     Environment variables needed...                      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Section 1: At-Risk Students Overview

**Purpose**: Quick statistics of students who need attention

**Displays**:
- **Low Attendance**: Students with attendance < 75%
- **Poor Performance**: Students with CGPA < 6.0
- **With Backlogs**: Students who have failed subjects

**Auto-updates**: Loads automatically when page opens

**Example**:
```
┌──────────────────┬──────────────────┬──────────────────┐
│       12         │        8         │        5         │
│ Low Attendance   │ Poor Performance │  With Backlogs   │
└──────────────────┴──────────────────┴──────────────────┘
```

## Section 2: Send Individual Notifications

**Purpose**: Send targeted alerts for specific students

### Step-by-Step Guide

**Step 1: Select Notification Type**
```
[Notification Type ▼]
  ├─ Low Attendance Alert
  └─ Poor Performance Alert
```

- **Low Attendance Alert**: For students with attendance < 75%
- **Poor Performance Alert**: For students with CGPA < 6.0

**Step 2: Enter Recipient Email**
```
[Recipient Email]
faculty@example.com
```

Who to send to:
- Faculty advisor
- Class teacher
- Parent email
- HOD email
- Any concerned person

**Step 3: Select Students**
```
[✓] Rahul Kumar (231FA00001) - SEC-1    Att: 65%
[✓] Priya Sharma (231FA00002) - SEC-2   Att: 70%
[ ] Amit Patel (231FA00003) - SEC-1     Att: 72%
```

- Check the boxes for students you want to notify about
- List updates based on notification type selected
- Shows relevant metric (attendance % or CGPA)

**Step 4: Send Notifications**
```
[Send Notifications]
```

- Click to send emails
- Wait for confirmation message
- Check for success/error feedback

### Example Workflow

**Scenario**: Send low attendance alerts for 3 students to their class teacher

1. Select "Low Attendance Alert" from dropdown
2. Enter "teacher@example.com" in recipient field
3. Check boxes for the 3 students
4. Click "Send Notifications"
5. See success message: "Successfully sent 3 notifications"
6. Teacher receives 3 separate emails (one per student)

## Section 3: Send Weekly Performance Report

**Purpose**: Send comprehensive summary report to management

### Step-by-Step Guide

**Step 1: Enter Recipient Email**
```
[Recipient Email]
hod@example.com
```

Who to send to:
- HOD (Head of Department)
- Principal
- Management
- Dean

**Step 2: Send Report**
```
[Send Report]
```

- Click to send bulk report
- Wait for confirmation
- Check for success message

### What's Included in Report

The bulk report includes:

**Overall Statistics:**
- Total students count
- Average CGPA
- Average attendance percentage

**Alert Counts:**
- Students with low attendance
- At-risk students (CGPA < 6 or attendance < 65)
- Students with backlogs

**Example Report Content:**
```
📊 Weekly Performance Report

Overall Statistics:
- Total Students: 150
- Average CGPA: 7.2
- Average Attendance: 82%

Alerts:
- Low Attendance: 12 students
- At Risk: 8 students
- With Backlogs: 5 students
```

## Section 4: Configuration

**Purpose**: Shows required environment variables

**Information Displayed:**
- SMTP server settings
- Required environment variables
- Link to Gmail App Password setup

**Note**: This is informational only - configuration is done in `.env` file

## Email Templates

### Low Attendance Alert Email

**Subject**: ⚠️ Low Attendance Alert - [Student Name]

**Content**:
```
Hi,

This is an automated alert regarding a student with low attendance:

┌─────────────────────────────────────────┐
│ Student Name: Rahul Kumar               │
│ Roll Number: 231FA00001                 │
│ Section: SEC-1                          │
│ Current Attendance: 65% ⚠️              │
│ CGPA: 7.2                               │
└─────────────────────────────────────────┘

Action Required: Please follow up with the student to improve attendance.

Generated on April 9, 2026 at 10:30 AM
```

### Poor Performance Alert Email

**Subject**: 📉 Performance Alert - [Student Name]

**Content**:
```
Hi,

This is an automated alert regarding a student with poor academic performance:

┌─────────────────────────────────────────┐
│ Student Name: Priya Sharma              │
│ Roll Number: 231FA00002                 │
│ Section: SEC-2                          │
│ CGPA: 5.8 ⚠️                            │
│ Backlogs: 2                             │
└─────────────────────────────────────────┘

Action Required: Please provide academic counseling and support to the student.

Generated on April 9, 2026 at 10:30 AM
```

### Weekly Performance Report Email

**Subject**: 📊 Weekly Performance Report - April 9, 2026

**Content**:
```
Hi,

Here's your weekly performance summary:

Overall Statistics:
┌─────────────────────────────────────────┐
│ Total Students: 150                     │
│ Average CGPA: 7.2                       │
│ Average Attendance: 82%                 │
└─────────────────────────────────────────┘

Alerts:
┌─────────────────────────────────────────┐
│ Low Attendance: 12 students             │
│ At Risk: 8 students                     │
│ With Backlogs: 5 students               │
└─────────────────────────────────────────┘

Please log in to the system for detailed reports and individual student information.

Generated on April 9, 2026 at 10:30 AM
```

## Common Use Cases

### Use Case 1: Weekly Faculty Alert

**Goal**: Send weekly alerts to faculty about low attendance students

**Steps**:
1. Navigate to `/notifications`
2. Select "Low Attendance Alert"
3. Enter faculty email: "faculty@example.com"
4. Select all students with attendance < 75%
5. Click "Send Notifications"
6. Faculty receives individual emails for each student

**Frequency**: Once per week (Monday morning)

### Use Case 2: Monthly HOD Report

**Goal**: Send monthly performance summary to HOD

**Steps**:
1. Navigate to `/notifications`
2. Scroll to "Weekly Performance Report"
3. Enter HOD email: "hod@example.com"
4. Click "Send Report"
5. HOD receives comprehensive summary

**Frequency**: Once per month (1st of month)

### Use Case 3: Parent Notification

**Goal**: Notify parents about their child's poor performance

**Steps**:
1. Navigate to `/notifications`
2. Select "Poor Performance Alert"
3. Enter parent email: "parent@example.com"
4. Select specific student
5. Click "Send Notifications"
6. Parent receives detailed alert

**Frequency**: As needed (when CGPA drops below 6.0)

### Use Case 4: Bulk Section Alert

**Goal**: Alert class teacher about all at-risk students in a section

**Steps**:
1. Navigate to `/notifications`
2. Select "Low Attendance Alert"
3. Enter teacher email: "teacher@example.com"
4. Select all students from SEC-1 with low attendance
5. Click "Send Notifications"
6. Teacher receives multiple emails (one per student)

**Frequency**: Bi-weekly (every 2 weeks)

## Tips and Best Practices

### Email Sending

1. **Check Spam Folder**: First-time emails may go to spam
2. **Batch Size**: Send max 50 students at once
3. **Rate Limits**: Gmail allows 500 emails/day
4. **Test First**: Send test email to yourself first
5. **Verify Recipients**: Double-check email addresses

### Notification Timing

1. **Morning Alerts**: Send between 9-11 AM
2. **Avoid Weekends**: Send on weekdays only
3. **Regular Schedule**: Maintain consistent timing
4. **Urgent Alerts**: Send immediately when needed
5. **Bulk Reports**: Send weekly or monthly

### Student Selection

1. **Review List**: Check student list before sending
2. **Verify Metrics**: Ensure attendance/CGPA is current
3. **Select Carefully**: Only select relevant students
4. **Avoid Duplicates**: Don't send multiple times
5. **Update Data**: Refresh data before sending

### Recipient Selection

1. **Appropriate Person**: Send to relevant faculty/parent
2. **Multiple Recipients**: Send separately to each
3. **CC/BCC**: Not supported (send individually)
4. **Verify Email**: Check email format is correct
5. **Test Email**: Send test to yourself first

## Troubleshooting

### Issue: "Failed to send notifications"

**Possible Causes**:
- Email configuration not set up
- Invalid App Password
- Network connection issue
- Gmail rate limit exceeded

**Solutions**:
1. Check `.env` file has email passwords
2. Verify App Passwords are correct
3. Check internet connection
4. Wait and try again (rate limit)
5. Run setup wizard: `python setup_email_notifications.py`

### Issue: "No students found for this category"

**Possible Causes**:
- No students meet the criteria
- Data not loaded yet
- Wrong notification type selected

**Solutions**:
1. Check "At-Risk Students Overview" section
2. Refresh the page
3. Try different notification type
4. Verify student data exists

### Issue: "Emails not received"

**Possible Causes**:
- Email in spam folder
- Wrong recipient email
- Email delivery delay
- Gmail blocking

**Solutions**:
1. Check spam/junk folder
2. Verify recipient email is correct
3. Wait 5-10 minutes
4. Check Gmail account activity
5. Send test email to yourself

### Issue: "Page loading slowly"

**Possible Causes**:
- Large number of students
- Slow database query
- Network latency

**Solutions**:
1. Wait for page to fully load
2. Refresh the page
3. Check network connection
4. Contact administrator

## Keyboard Shortcuts

- **Ctrl+R**: Refresh page
- **Tab**: Navigate between fields
- **Space**: Toggle checkbox
- **Enter**: Submit form (when in input field)

## Mobile Usage

The notifications page is responsive and works on mobile devices:

1. **Portrait Mode**: Sections stack vertically
2. **Landscape Mode**: Better layout for forms
3. **Touch**: Tap to select students
4. **Scroll**: Swipe to scroll student list
5. **Zoom**: Pinch to zoom if needed

## Security Notes

1. **Access Control**: Only DEO and Admin can access
2. **Email Privacy**: Recipient emails not stored
3. **Student Data**: Handled securely
4. **Audit Trail**: Email sending logged
5. **Session Timeout**: Auto-logout after 15 minutes

## Related Documentation

- `EMAIL_NOTIFICATION_GUIDE.md` - Complete setup guide
- `EMAIL_AND_TIMEOUT_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `SESSION_TIMEOUT_GUIDE.md` - Timeout configuration
- `CONSOLE_GUIDE.md` - Console page usage

## Support

For help or questions:
1. Check this guide first
2. Review error messages
3. Check spam folder
4. Run setup wizard
5. Contact system administrator

---

**Quick Reference**:
- **URL**: `/notifications`
- **Access**: DEO, Admin only
- **Email Limit**: 500/day (Gmail)
- **Batch Size**: Max 50 students
- **Session Timeout**: 15 minutes
