"""
Test login validation to ensure OTP codes work correctly
"""
import pyotp
from werkzeug.security import check_password_hash
import mysql.connector

# Database connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='nandu3742L@',
    database='deo_chatbot'
)

# Get user from database
cur = conn.cursor()
cur.execute("SELECT username, password, otp_secret FROM users WHERE username='deo_cse'")
row = cur.fetchone()

if row:
    username, hashed_password, otp_secret = row
    
    print("=" * 70)
    print("LOGIN VALIDATION TEST")
    print("=" * 70)
    
    # Test password
    test_password = "cse123"
    password_valid = check_password_hash(hashed_password, test_password)
    
    print(f"\n✅ Username: {username}")
    print(f"✅ Password Test: {'PASS' if password_valid else 'FAIL'}")
    print(f"✅ OTP Secret: {otp_secret}")
    
    # Generate current OTP
    totp = pyotp.TOTP(otp_secret)
    current_otp = totp.now()
    
    print(f"\n🔐 Current OTP Code: {current_otp}")
    print(f"⏰ This code is valid for the next 30 seconds")
    
    # Test OTP validation with different windows
    print(f"\n📊 OTP Validation Test:")
    print(f"   - Valid with window=0: {totp.verify(current_otp, valid_window=0)}")
    print(f"   - Valid with window=1: {totp.verify(current_otp, valid_window=1)}")
    print(f"   - Valid with window=2: {totp.verify(current_otp, valid_window=2)}")
    
    # Test with user input
    print(f"\n" + "=" * 70)
    user_otp = input("Enter OTP from Microsoft Authenticator: ").strip()
    
    if totp.verify(user_otp, valid_window=1):
        print("✅ SUCCESS! OTP is valid!")
        print("Your Microsoft Authenticator is working correctly.")
    else:
        print("❌ FAILED! OTP is invalid.")
        print(f"Expected: {current_otp}")
        print(f"You entered: {user_otp}")
        print("\nPossible issues:")
        print("1. Time sync issue - make sure phone time is automatic")
        print("2. Wrong account - make sure you're looking at 'deo_cse' in the app")
        print("3. Code expired - wait for next code and try again")
    
    print("=" * 70)

cur.close()
conn.close()
