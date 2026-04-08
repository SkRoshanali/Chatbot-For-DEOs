# Microsoft Authenticator Setup Guide

## ✅ Yes, Microsoft Authenticator Works!

Both Google Authenticator and Microsoft Authenticator use the same **TOTP (Time-based One-Time Password)** standard, so they are 100% compatible.

## 📱 How to Set Up Microsoft Authenticator

### Method 1: Scan QR Code (Recommended)

1. **Open the Admin Setup Page**
   - Go to: http://localhost:5000/login
   - Click the "🔑 Administrator" tab
   - Enter master password: `Admin@123`
   - Click "Access Setup"

2. **Generate QR Code**
   - Click "🔐 Generate QR Code" for the user you want (e.g., deo_cse)
   - A QR code will appear

3. **Scan with Microsoft Authenticator**
   - Open Microsoft Authenticator app on your phone
   - Tap the "+" button (top right)
   - Select "Other account (Google, Facebook, etc.)"
   - Scan the QR code displayed on screen
   - Done! The account will be added with 6-digit codes

### Method 2: Manual Entry (If QR doesn't work)

1. **Get the Secret Key**
   - From the database, the secrets are:
     - **deo_cse**: `S36ATIZCBRFONCYENSKGEAC4SRZG72UV`
     - **hod_cse**: `XK6NETWDOZ2XQMNHRGESW5SAYWZH67SA`
     - **admin**: `P6HHTAKNUTVKOOS7GZ4MTNSB6YHB3XQH`

2. **Add to Microsoft Authenticator**
   - Open Microsoft Authenticator app
   - Tap "+" → "Other account"
   - Tap "Or enter code manually"
   - Enter:
     - **Account name**: deo_cse (or the username you want)
     - **Secret key**: (paste the secret from above)
     - **Type of account**: Time based
   - Tap "Finish"

## 🔐 Login Process

1. Open http://localhost:5000/login
2. Enter credentials:
   - Username: `deo_cse`
   - Password: `cse123`
   - Department: `CSE`
3. Open Microsoft Authenticator app
4. Find "deo_cse" account
5. Copy the 6-digit code (it changes every 30 seconds)
6. Paste in OTP field
7. Click "Sign In"

## 📋 All User Accounts

| Username | Password  | Role  | Department |
|----------|-----------|-------|------------|
| deo_cse  | cse123    | DEO   | CSE        |
| hod_cse  | hod123    | HOD   | CSE        |
| admin    | admin123  | Admin | ALL        |

## ⚠️ Important Notes

- OTP codes change every 30 seconds
- Both apps (Google & Microsoft Authenticator) will show the same code at the same time
- If login fails, wait for the next code cycle
- Make sure your phone's time is synchronized (Settings → Date & Time → Automatic)

## 🆘 Troubleshooting

### "Invalid OTP" Error
- **Cause**: Time sync issue or expired code
- **Fix**: 
  1. Make sure phone time is set to automatic
  2. Wait for the next code (watch the countdown in the app)
  3. Enter the code immediately after it refreshes

### QR Code Not Scanning
- **Fix**: Use Method 2 (Manual Entry) instead

### Code Not Working
- **Fix**: Check if you're using the correct username/password first
- The error "Invalid username or password" means credentials are wrong
- The error "Invalid OTP" means credentials are correct but OTP is wrong

## 🎯 Quick Test

You can also use the LOGIN_INSTRUCTIONS.html file I created - it shows live OTP codes in your browser without needing the phone app (useful for testing).

Open: `chatbot/LOGIN_INSTRUCTIONS.html` in your browser
