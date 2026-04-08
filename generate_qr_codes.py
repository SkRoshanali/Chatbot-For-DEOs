"""
Generate QR codes for Microsoft Authenticator setup
Run this script to get QR codes for all users
"""
import pyotp
import qrcode
import os

# User credentials from database
users = {
    'deo_cse': {
        'secret': 'S36ATIZCBRFONCYENSKGEAC4SRZG72UV',
        'password': 'cse123',
        'role': 'DEO'
    },
    'hod_cse': {
        'secret': 'XK6NETWDOZ2XQMNHRGESW5SAYWZH67SA',
        'password': 'hod123',
        'role': 'HOD'
    },
    'admin': {
        'secret': 'P6HHTAKNUTVKOOS7GZ4MTNSB6YHB3XQH',
        'password': 'admin123',
        'role': 'Admin'
    }
}

print("=" * 70)
print("MICROSOFT AUTHENTICATOR QR CODE GENERATOR")
print("=" * 70)
print("\nGenerating QR codes for all users...")
print("Scan these with Microsoft Authenticator app\n")

# Create qr_codes directory if it doesn't exist
os.makedirs('qr_codes', exist_ok=True)

for username, info in users.items():
    # Generate TOTP URI
    totp = pyotp.TOTP(info['secret'])
    uri = totp.provisioning_uri(
        name=username,
        issuer_name='DEO Chatbot'
    )
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    # Save QR code as image
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f'qr_codes/{username}_qr.png'
    img.save(filename)
    
    # Get current OTP
    current_otp = totp.now()
    
    print(f"\n{'='*70}")
    print(f"👤 {username.upper()} ({info['role']})")
    print(f"{'='*70}")
    print(f"Password:     {info['password']}")
    print(f"Secret Key:   {info['secret']}")
    print(f"Current OTP:  {current_otp}")
    print(f"QR Code:      {filename}")
    print(f"\n📱 Scan this QR code with Microsoft Authenticator:")
    print(f"   1. Open Microsoft Authenticator")
    print(f"   2. Tap '+' → 'Other account'")
    print(f"   3. Scan the QR code from: {filename}")
    print(f"\n🔗 Or enter manually:")
    print(f"   Account name: {username}")
    print(f"   Secret key:   {info['secret']}")
    print(f"   Type:         Time based")

print("\n" + "="*70)
print("✅ QR codes saved in 'qr_codes/' folder")
print("="*70)
print("\n📂 Open the 'qr_codes' folder to see all QR code images")
print("📱 Scan them with Microsoft Authenticator app\n")

# Open the folder
try:
    import subprocess
    subprocess.run(['explorer', 'qr_codes'], check=False)
    print("✅ QR codes folder opened!")
except:
    print("💡 Manually open the 'qr_codes' folder to see the images")
