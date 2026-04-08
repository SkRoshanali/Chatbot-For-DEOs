"""
Verify OTP synchronization between server and Microsoft Authenticator
This script shows the current OTP and validates user input
"""
import pyotp
import time
import os

# Clear screen
os.system('cls' if os.name == 'nt' else 'clear')

# OTP secrets from database
secrets = {
    'deo_cse': 'S36ATIZCBRFONCYENSKGEAC4SRZG72UV',
    'hod_cse': 'XK6NETWDOZ2XQMNHRGESW5SAYWZH67SA',
    'admin': 'P6HHTAKNUTVKOOS7GZ4MTNSB6YHB3XQH'
}

print("=" * 80)
print("OTP SYNCHRONIZATION CHECKER")
print("=" * 80)
print("\nThis tool helps verify your Microsoft Authenticator is synced correctly.\n")

# Select user
print("Select user:")
print("1. deo_cse")
print("2. hod_cse")
print("3. admin")
choice = input("\nEnter choice (1-3): ").strip()

user_map = {'1': 'deo_cse', '2': 'hod_cse', '3': 'admin'}
username = user_map.get(choice, 'deo_cse')
secret = secrets[username]

print(f"\n{'='*80}")
print(f"Testing OTP for: {username}")
print(f"{'='*80}\n")

totp = pyotp.TOTP(secret)

# Show live OTP updates
print("📱 Live OTP codes (press Ctrl+C to stop):\n")
print("Compare these with your Microsoft Authenticator app:")
print("-" * 80)

try:
    while True:
        current_otp = totp.now()
        
        # Calculate time remaining
        epoch = int(time.time())
        remaining = 30 - (epoch % 30)
        
        # Progress bar
        progress = int((remaining / 30) * 40)
        bar = "█" * progress + "░" * (40 - progress)
        
        print(f"\r🔐 Current OTP: {current_otp}  |  {bar}  {remaining}s ", end='', flush=True)
        
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\n\n" + "="*80)
    print("MANUAL OTP VALIDATION TEST")
    print("="*80)
    
    current_otp = totp.now()
    print(f"\n✅ Current server OTP: {current_otp}")
    print(f"⏰ Valid for next {30 - (int(time.time()) % 30)} seconds\n")
    
    user_otp = input("Enter OTP from Microsoft Authenticator: ").strip()
    
    print("\n" + "="*80)
    print("VALIDATION RESULTS")
    print("="*80)
    
    # Test with different windows
    results = []
    for window in [0, 1, 2]:
        valid = totp.verify(user_otp, valid_window=window)
        results.append((window, valid))
        status = "✅ VALID" if valid else "❌ INVALID"
        print(f"Window {window} ({window*30}s tolerance): {status}")
    
    print("\n" + "="*80)
    
    if any(r[1] for r in results):
        print("✅ SUCCESS! Your Microsoft Authenticator is working correctly!")
        print("You can now login to the application.")
    else:
        print("❌ FAILED! OTP codes don't match.")
        print(f"\nExpected: {current_otp}")
        print(f"You entered: {user_otp}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure your phone's time is set to AUTOMATIC")
        print("   (Settings → Date & Time → Set Automatically)")
        print("2. Make sure you're looking at the correct account in the app")
        print(f"   (Should show '{username}' or 'DEO Chatbot')")
        print("3. Wait for the code to refresh and try again")
        print("4. Try re-scanning the QR code from qr_codes/ folder")
    
    print("="*80 + "\n")
