"""
Show current OTP codes for all users
"""
import pyotp
import time

secrets = {
    'deo_cse': 'S36ATIZCBRFONCYENSKGEAC4SRZG72UV',
    'hod_cse': 'XK6NETWDOZ2XQMNHRGESW5SAYWZH67SA',
    'admin': 'P6HHTAKNUTVKOOS7GZ4MTNSB6YHB3XQH'
}

print("=" * 80)
print("CURRENT OTP CODES - Compare with Microsoft Authenticator")
print("=" * 80)

epoch = int(time.time())
remaining = 30 - (epoch % 30)

print(f"\n⏰ These codes are valid for the next {remaining} seconds\n")

for username, secret in secrets.items():
    totp = pyotp.TOTP(secret)
    current_otp = totp.now()
    print(f"👤 {username:12} → {current_otp}")

print("\n" + "=" * 80)
print("📱 Open Microsoft Authenticator and compare the codes")
print("   They should match EXACTLY")
print("=" * 80)
