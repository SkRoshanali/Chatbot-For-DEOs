#!/usr/bin/env python3
"""
Email Notification Setup Script for Smart DEO
This script helps configure and test email notifications with role-based senders.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from email_service import test_email_config, send_email, ROLE_EMAILS

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_step(number, text):
    """Print formatted step"""
    print(f"\n[Step {number}] {text}")
    print("-" * 70)

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("⚠️  WARNING: .env file not found!")
        print("\nPlease create a .env file by copying .env.example:")
        print("  cp .env.example .env")
        print("\nThen edit .env and add your email App Passwords.")
        return False
    return True

def test_role_config(role):
    """Test email configuration for a specific role"""
    print(f"\n🔍 Testing {role} configuration...")
    
    config = ROLE_EMAILS.get(role)
    if not config:
        print(f"❌ Role {role} not found in configuration")
        return False
    
    email = config['email']
    password = config['password']
    
    print(f"   Email: {email}")
    
    if not password:
        print(f"   ❌ Password not configured")
        print(f"   Please set {role.upper()}_EMAIL_PASSWORD in .env file")
        return False
    
    print(f"   ✅ Password configured ({len(password)} characters)")
    return True

def send_test_email(role, recipient):
    """Send a test email from a specific role"""
    print(f"\n📧 Sending test email from {role} to {recipient}...")
    
    subject = f"Test Email from Smart DEO - {role}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #f5f5f5; padding: 30px; border-radius: 10px;">
            <h2 style="color: #667eea;">✅ Email Configuration Test</h2>
            
            <p>This is a test email from the Smart DEO system.</p>
            
            <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Sender Role:</strong> {role}</p>
                <p style="margin: 5px 0;"><strong>Sender Email:</strong> {ROLE_EMAILS[role]['email']}</p>
                <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: green;">✅ Working</span></p>
            </div>
            
            <p>If you received this email, your email notification system is configured correctly!</p>
            
            <p style="margin-top: 30px; color: #6c757d; font-size: 0.9em;">
                This is a test message from Smart DEO System.
            </p>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Email Configuration Test
    
    Sender Role: {role}
    Sender Email: {ROLE_EMAILS[role]['email']}
    Status: Working
    
    If you received this email, your email notification system is configured correctly!
    """
    
    try:
        success = send_email(recipient, subject, html, text, role)
        if success:
            print(f"   ✅ Test email sent successfully!")
            print(f"   Check {recipient} inbox (and spam folder)")
            return True
        else:
            print(f"   ❌ Failed to send test email")
            print(f"   Check the error messages above")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def main():
    """Main setup wizard"""
    print_header("Smart DEO - Email Notification Setup Wizard")
    
    print("This wizard will help you configure and test email notifications.")
    print("You'll need Gmail App Passwords for each role (DEO, HOD, Admin).")
    
    # Step 1: Check .env file
    print_step(1, "Checking Environment Configuration")
    if not check_env_file():
        sys.exit(1)
    
    print("✅ .env file found")
    
    # Step 2: Test each role configuration
    print_step(2, "Testing Role-Based Email Configuration")
    
    roles_status = {}
    for role in ['DEO', 'HOD', 'Admin']:
        roles_status[role] = test_role_config(role)
    
    configured_roles = [role for role, status in roles_status.items() if status]
    
    if not configured_roles:
        print("\n❌ No roles configured!")
        print("\nPlease add App Passwords to your .env file:")
        print("  DEO_EMAIL_PASSWORD=your_app_password")
        print("  HOD_EMAIL_PASSWORD=your_app_password")
        print("  ADMIN_EMAIL_PASSWORD=your_app_password")
        print("\nGenerate App Passwords at: https://myaccount.google.com/apppasswords")
        sys.exit(1)
    
    print(f"\n✅ {len(configured_roles)} role(s) configured: {', '.join(configured_roles)}")
    
    # Step 3: Send test emails
    print_step(3, "Sending Test Emails")
    
    print("\nWould you like to send test emails? (y/n): ", end='')
    response = input().strip().lower()
    
    if response == 'y':
        print("\nEnter recipient email address for test: ", end='')
        recipient = input().strip()
        
        if not recipient or '@' not in recipient:
            print("❌ Invalid email address")
            sys.exit(1)
        
        print(f"\nSending test emails to {recipient}...")
        
        success_count = 0
        for role in configured_roles:
            if send_test_email(role, recipient):
                success_count += 1
        
        print(f"\n{'='*70}")
        print(f"  Test Results: {success_count}/{len(configured_roles)} successful")
        print(f"{'='*70}")
        
        if success_count == len(configured_roles):
            print("\n🎉 All tests passed! Email notifications are ready to use.")
        elif success_count > 0:
            print(f"\n⚠️  Some tests failed. Check the error messages above.")
        else:
            print("\n❌ All tests failed. Please check your configuration.")
    
    # Step 4: Configuration summary
    print_step(4, "Configuration Summary")
    
    print("\n📋 Email Addresses:")
    for role in ['DEO', 'HOD', 'Admin']:
        config = ROLE_EMAILS[role]
        status = "✅ Configured" if roles_status.get(role) else "❌ Not configured"
        print(f"   {role:6} → {config['email']:25} {status}")
    
    print("\n📚 Next Steps:")
    print("   1. Navigate to /notifications page in the application")
    print("   2. Select students and notification type")
    print("   3. Enter recipient email and send")
    print("   4. Check recipient inbox (and spam folder)")
    
    print("\n📖 For detailed documentation, see: EMAIL_NOTIFICATION_GUIDE.md")
    
    print("\n" + "="*70)
    print("  Setup Complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        sys.exit(1)
