"""
Quick test to verify login credentials and generate current OTP
"""
import pyotp
from werkzeug.security import check_password_hash

# Test credentials from seed_data
users = {
    'deo_cse': {
        'password': 'cse123',
        'otp_secret': 'S36ATIZCBRFONCYENSKGEAC4SRZG72UV'
    },
    'hod_cse': {
        'password': 'hod123',
        'otp_secret': 'XK6NETWDOZ2XQMNHRGESW5SAYWZH67SA'
    },
    'admin': {
        'password': 'admin123',
        'otp_secret': 'P6HHTAKNUTVKOOS7GZ4MTNSB6YHB3XQH'
    }
}

print("=" * 60)
print("LOGIN CREDENTIALS FOR DEO CHATBOT")
print("=" * 60)

for username, creds in users.items():
    totp = pyotp.TOTP(creds['otp_secret'])
    current_otp = totp.now()
    
    print(f"\nUsername: {username}")
    print(f"Password: {creds['password']}")
    print(f"Current OTP: {current_otp}")
    print(f"OTP Secret: {creds['otp_secret']}")
    print("-" * 60)

print("\nNOTE: OTP changes every 30 seconds!")
print("Use the current OTP shown above to login.")
