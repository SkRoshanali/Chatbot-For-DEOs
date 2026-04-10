#!/usr/bin/env python3
"""
Email Configuration Test Script
Tests email sending functionality for all roles (DEO, HOD, Admin)
"""

import os
import sys
from email_service import test_email_config, send_email, ROLE_EMAILS

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def test_role_config(role):
    """Test configuration for a specific role"""
    print(f"Testing {role} configuration...")
    
    config = ROLE_EMAILS.get(role)
    if not config:
        print(f"  ❌ Role '{role}' not found in configuration")
        return False
    
    email = config['email']
    password = config['password']
    name = config['name']
    
    print(f"  Email: {email}")
    print(f"  Name: {name}")
    
    if not password:
        print(f"  ❌ Password not configured")
        print(f"  → Set {role.upper()}_EMAIL_PASSWORD in .env file")
        return False
    
    print(f"  ✅ Password configured (length: {len(password)})")
    return True

def send_test_email(role, recipient):
    """Send a test email from a specific role"""
    print(f"\nSending test email from {role} to {recipient}...")
    
    subject = f"Test Email from Smart DEO - {role}"
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #667eea;">✅ Email Configuration Test</h2>
        <p>This is a test email from the Smart DEO system.</p>
        <div style="background: #e7f3ff; padding: 15px; border-left: 4px solid #667eea; margin: 20px 0;">
            <p><strong>Sender Role:</strong> {role}</p>
            <p><strong>Email Address:</strong> {ROLE_EMAILS[role]['email']}</p>
            <p><strong>Status:</strong> Email configuration is working correctly! ✅</p>
        </div>
        <p>If you received this email, your email notification system is configured properly.</p>
        <p style="color: #6c757d; font-size: 0.9em; margin-top: 30px;">
            Smart DEO System - Email Configuration Test
        </p>
    </body>
    </html>
    """
    
    text = f"""
    Email Configuration Test
    
    This is a test email from the Smart DEO system.
    
    Sender Role: {role}
    Email Address: {ROLE_EMAILS[role]['email']}
    Status: Email configuration is working correctly!
    
    If you received this email, your email notification system is configured properly.
    
    Smart DEO System - Email Configuration Test
    """
    
    try:
        success = send_email(recipient, subject, html, text, role)
        if success:
            print(f"  ✅ Test email sent successfully!")
            return True
        else:
            print(f"  ❌ Failed to send test email")
            return False
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False

def main():
    """Main test function"""
    print_header("Smart DEO Email Configuration Test")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  Warning: .env file not found")
        print("   Create .env file from .env.example and add email passwords")
        print("   Example:")
        print("   DEO_EMAIL_PASSWORD=your_app_password")
        print("   HOD_EMAIL_PASSWORD=your_app_password")
        print("   ADMIN_EMAIL_PASSWORD=your_app_password")
        print()
    
    # Test configuration for all roles
    print_header("Configuration Check")
    
    roles_status = {}
    for role in ['DEO', 'HOD', 'Admin']:
        roles_status[role] = test_role_config(role)
        print()
    
    # Summary
    print_header("Configuration Summary")
    
    configured_count = sum(1 for status in roles_status.values() if status)
    total_count = len(roles_status)
    
    for role, status in roles_status.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {role}: {'Configured' if status else 'Not Configured'}")
    
    print(f"\n  {configured_count}/{total_count} roles configured")
    
    if configured_count == 0:
        print("\n❌ No roles configured. Please set email passwords in .env file.")
        print("\nSetup Instructions:")
        print("1. Copy .env.example to .env")
        print("2. Generate App Passwords for each Gmail account:")
        print("   - Go to https://myaccount.google.com/security")
        print("   - Enable 2-Step Verification")
        print("   - Generate App Password for 'Mail' → 'Other (Smart DEO)'")
        print("3. Add passwords to .env file:")
        print("   DEO_EMAIL_PASSWORD=your_16_char_password")
        print("   HOD_EMAIL_PASSWORD=your_16_char_password")
        print("   ADMIN_EMAIL_PASSWORD=your_16_char_password")
        return
    
    # Ask if user wants to send test emails
    print("\n" + "-"*60)
    send_test = input("\nDo you want to send test emails? (y/n): ").strip().lower()
    
    if send_test == 'y':
        recipient = input("Enter recipient email address: ").strip()
        
        if not recipient or '@' not in recipient:
            print("❌ Invalid email address")
            return
        
        print_header("Sending Test Emails")
        
        for role, status in roles_status.items():
            if status:
                send_test_email(role, recipient)
                print()
        
        print_header("Test Complete")
        print(f"Check {recipient} inbox for test emails")
        print("If you don't see them, check spam folder")
    
    print("\n✅ Email configuration test complete!")
    print("\nNext steps:")
    print("1. Start the application: uvicorn main:app --reload")
    print("2. Login and navigate to /notifications")
    print("3. Send real notifications to faculty/students")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
