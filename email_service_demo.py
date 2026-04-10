"""
Demo Email Service for Smart DEO - Competition Version
This version simulates email sending for demonstration purposes
"""
import os
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

# Demo mode flag
DEMO_MODE = os.environ.get('EMAIL_DEMO_MODE', 'true').lower() == 'true'

class EmailLog:
    """Store sent emails for demo purposes"""
    sent_emails = []
    
    @classmethod
    def add(cls, email_data):
        cls.sent_emails.append({
            **email_data,
            'timestamp': datetime.now().isoformat()
        })
    
    @classmethod
    def get_all(cls):
        return cls.sent_emails
    
    @classmethod
    def clear(cls):
        cls.sent_emails = []

def send_email_demo(to_email: str, subject: str, body_html: str, body_text: str = None, sender_role: str = 'DEO') -> bool:
    """
    Demo email sending - logs emails instead of actually sending
    Perfect for demonstrations and competitions
    """
    role_emails = {
        'DEO': '231fa04436@gmail.com',
        'HOD': '231fa04476@gmail.com',
        'Admin': '231fa04446@gmail.com'
    }
    
    from_email = role_emails.get(sender_role, role_emails['DEO'])
    
    email_data = {
        'from': f"{sender_role} - Smart DEO <{from_email}>",
        'to': to_email,
        'subject': subject,
        'body_html': body_html,
        'body_text': body_text or 'Email content',
        'sender_role': sender_role,
        'status': 'sent'
    }
    
    EmailLog.add(email_data)
    
    print(f"[Demo Email] ✅ Sent from {sender_role} to {to_email}: {subject}")
    return True

def send_low_attendance_alert_demo(student: Dict, recipient_email: str, sender_role: str = 'DEO') -> bool:
    """Demo version of low attendance alert"""
    subject = f"⚠️ Low Attendance Alert - {student['name']}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #dc3545; margin-bottom: 20px;">⚠️ Low Attendance Alert</h2>
            
            <p>Dear Faculty,</p>
            
            <p>This is an automated alert regarding a student with low attendance:</p>
            
            <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Student Name:</strong> {student['name']}</p>
                <p style="margin: 5px 0;"><strong>Roll Number:</strong> {student['roll']}</p>
                <p style="margin: 5px 0;"><strong>Section:</strong> {student.get('section', 'N/A')}</p>
                <p style="margin: 5px 0;"><strong>Current Attendance:</strong> <span style="color: #dc3545; font-weight: bold;">{student.get('attendance', 0)}%</span></p>
                <p style="margin: 5px 0;"><strong>CGPA:</strong> {student.get('cgpa', 0)}</p>
            </div>
            
            <p><strong>Action Required:</strong> Please follow up with the student to improve attendance.</p>
            
            <p style="margin-top: 30px; color: #6c757d; font-size: 0.9em;">
                This is an automated message from Smart DEO System.<br>
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Low Attendance Alert
    
    Student Name: {student['name']}
    Roll Number: {student['roll']}
    Section: {student.get('section', 'N/A')}
    Current Attendance: {student.get('attendance', 0)}%
    CGPA: {student.get('cgpa', 0)}
    
    Action Required: Please follow up with the student to improve attendance.
    
    Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    """
    
    return send_email_demo(recipient_email, subject, html, text, sender_role)

def send_poor_performance_alert_demo(student: Dict, recipient_email: str, sender_role: str = 'DEO') -> bool:
    """Demo version of poor performance alert"""
    subject = f"📉 Performance Alert - {student['name']}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #dc3545; margin-bottom: 20px;">📉 Performance Alert</h2>
            
            <p>Dear Faculty,</p>
            
            <p>This is an automated alert regarding a student with poor academic performance:</p>
            
            <div style="background: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Student Name:</strong> {student['name']}</p>
                <p style="margin: 5px 0;"><strong>Roll Number:</strong> {student['roll']}</p>
                <p style="margin: 5px 0;"><strong>Section:</strong> {student.get('section', 'N/A')}</p>
                <p style="margin: 5px 0;"><strong>CGPA:</strong> <span style="color: #dc3545; font-weight: bold;">{student.get('cgpa', 0)}</span></p>
                <p style="margin: 5px 0;"><strong>Backlogs:</strong> {student.get('backlogs', 0)}</p>
            </div>
            
            <p><strong>Action Required:</strong> Please provide academic counseling and support to the student.</p>
            
            <p style="margin-top: 30px; color: #6c757d; font-size: 0.9em;">
                This is an automated message from Smart DEO System.<br>
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Performance Alert
    
    Student Name: {student['name']}
    Roll Number: {student['roll']}
    Section: {student.get('section', 'N/A')}
    CGPA: {student.get('cgpa', 0)}
    Backlogs: {student.get('backlogs', 0)}
    
    Action Required: Please provide academic counseling and support to the student.
    
    Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    """
    
    return send_email_demo(recipient_email, subject, html, text, sender_role)

def send_bulk_report_demo(recipient_email: str, report_data: Dict, sender_role: str = 'DEO') -> bool:
    """Demo version of bulk report"""
    subject = f"📊 Weekly Performance Report - {datetime.now().strftime('%B %d, %Y')}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #667eea; margin-bottom: 20px;">📊 Weekly Performance Report</h2>
            
            <p>Dear Faculty,</p>
            
            <p>Here's your weekly performance summary:</p>
            
            <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #667eea;">Overall Statistics</h3>
                <p style="margin: 5px 0;"><strong>Total Students:</strong> {report_data.get('total_students', 0)}</p>
                <p style="margin: 5px 0;"><strong>Average CGPA:</strong> {report_data.get('avg_cgpa', 0)}</p>
                <p style="margin: 5px 0;"><strong>Average Attendance:</strong> {report_data.get('avg_attendance', 0)}%</p>
            </div>
            
            <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #856404;">Alerts</h3>
                <p style="margin: 5px 0;"><strong>Low Attendance:</strong> {report_data.get('low_attendance', 0)} students</p>
                <p style="margin: 5px 0;"><strong>At Risk:</strong> {report_data.get('at_risk', 0)} students</p>
                <p style="margin: 5px 0;"><strong>With Backlogs:</strong> {report_data.get('with_backlogs', 0)} students</p>
            </div>
            
            <p>Please log in to the system for detailed reports and individual student information.</p>
            
            <p style="margin-top: 30px; color: #6c757d; font-size: 0.9em;">
                This is an automated weekly report from Smart DEO System.<br>
                Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Weekly Performance Report
    
    Overall Statistics:
    - Total Students: {report_data.get('total_students', 0)}
    - Average CGPA: {report_data.get('avg_cgpa', 0)}
    - Average Attendance: {report_data.get('avg_attendance', 0)}%
    
    Alerts:
    - Low Attendance: {report_data.get('low_attendance', 0)} students
    - At Risk: {report_data.get('at_risk', 0)} students
    - With Backlogs: {report_data.get('with_backlogs', 0)} students
    
    Please log in to the system for detailed reports.
    
    Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    """
    
    return send_email_demo(recipient_email, subject, html, text, sender_role)

# Export functions based on mode
if DEMO_MODE:
    send_low_attendance_alert = send_low_attendance_alert_demo
    send_poor_performance_alert = send_poor_performance_alert_demo
    send_bulk_report = send_bulk_report_demo
    print("[Email Service] Running in DEMO MODE - emails will be logged, not sent")
else:
    from email_service import (
        send_low_attendance_alert as _smtp_low,
        send_poor_performance_alert as _smtp_perf,
        send_bulk_report as _smtp_bulk,
        SMTP_EMAIL
    )

    def send_low_attendance_alert(student, recipient_email, sender_role='DEO'):
        success = _smtp_low(student, recipient_email, sender_role)
        EmailLog.add({
            'from': f"{sender_role} - Smart DEO <{SMTP_EMAIL}>",
            'to': recipient_email,
            'subject': f"⚠️ Low Attendance Alert - {student['name']}",
            'body_html': f"<p>Low attendance: {student['name']} ({student['roll']}) — {student.get('attendance',0)}%</p>",
            'body_text': f"Low attendance alert for {student['name']}",
            'sender_role': sender_role,
            'status': 'sent' if success else 'failed'
        })
        return success

    def send_poor_performance_alert(student, recipient_email, sender_role='DEO'):
        success = _smtp_perf(student, recipient_email, sender_role)
        EmailLog.add({
            'from': f"{sender_role} - Smart DEO <{SMTP_EMAIL}>",
            'to': recipient_email,
            'subject': f"📉 Performance Alert - {student['name']}",
            'body_html': f"<p>Performance alert: {student['name']} ({student['roll']}) — CGPA: {student.get('cgpa',0)}</p>",
            'body_text': f"Performance alert for {student['name']}",
            'sender_role': sender_role,
            'status': 'sent' if success else 'failed'
        })
        return success

    def send_bulk_report(recipient_email, report_data, sender_role='DEO'):
        success = _smtp_bulk(recipient_email, report_data, sender_role)
        EmailLog.add({
            'from': f"{sender_role} - Smart DEO <{SMTP_EMAIL}>",
            'to': recipient_email,
            'subject': f"📊 Weekly Performance Report",
            'body_html': f"<p>Bulk report: {report_data.get('total_students',0)} students</p>",
            'body_text': "Bulk report sent",
            'sender_role': sender_role,
            'status': 'sent' if success else 'failed'
        })
        return success

    print("[Email Service] Running in PRODUCTION MODE - emails sent via SMTP")
