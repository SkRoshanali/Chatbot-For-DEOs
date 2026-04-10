# How to Start Smart DEO — Complete Guide

## ✅ One-Time Setup (do this only ONCE)

### 1. Make sure MySQL is installed and running
- Open XAMPP → Start MySQL
- OR open Windows Services → Start MySQL

### 2. Open terminal inside the `chatbot` folder
```
Right-click inside chatbot folder → Open in Terminal
```
Or:
```bash
cd C:\path\to\your\chatbot
```

### 3. Install Python packages
```bash
pip install -r requirements.txt
```

---

## 🚀 Every Time You Want to Start

### Step 1 — Start MySQL
Make sure MySQL is running (XAMPP or Windows Services)

### Step 2 — Open terminal in the `chatbot` folder

### Step 3 — Run this command
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

### Step 4 — Open browser and go to
```
http://localhost:5000
```

---

## 🔑 Login Credentials

| Username  | Password  | Department | Role  |
|-----------|-----------|------------|-------|
| deo_cse   | cse123    | CSE        | DEO   |
| hod_cse   | hod123    | CSE        | HOD   |
| admin     | admin123  | CSE        | Admin |

OTP: Use Microsoft Authenticator or Google Authenticator app
(Scan QR code at http://localhost:5000/setup if not set up yet)

---

## 🔗 All Links

| Link                              | What it does              |
|-----------------------------------|---------------------------|
| http://localhost:5000/            | Home (auto-redirect)      |
| http://localhost:5000/login       | Login page                |
| http://localhost:5000/console     | **Main Console (NEW!)**   |
| http://localhost:5000/chat        | Main chatbot              |
| http://localhost:5000/dashboard   | Visual Dashboard (NEW!)   |
| http://localhost:5000/data        | Data management           |
| http://localhost:5000/notifications| Email Notifications (NEW!)|
| http://localhost:5000/admin/db    | View database (all tables)|
| http://localhost:5000/setup       | Admin setup / QR codes    |
| http://localhost:5000/logout      | Logout                    |

**💡 Pro Tip:** Just remember http://localhost:5000/console - it has links to everything!

---

## 🗄️ Database Info

- Type: MySQL
- Database name: deo_chatbot
- Host: localhost
- Port: 3306
- User: root
- Password: nandu3742L@

Tables:
- students       → all student records
- subject_marks  → per-subject marks (CN, SE, ADS, PDC)
- users          → login accounts

---

## ❌ Common Problems & Fixes

| Problem                              | Fix                                              |
|--------------------------------------|--------------------------------------------------|
| mysql.connector error                | MySQL is not running — start it first            |
| ModuleNotFoundError                  | Run: pip install -r requirements.txt             |
| Address already in use (port 5000)   | Change port: --port 5001                         |
| Page not loading                     | Make sure you're in the chatbot folder           |
| OTP not working                      | Re-scan QR at http://localhost:5000/setup        |
| Changes not showing in browser       | Hard refresh: Ctrl + Shift + R                   |
| Can't login                          | Check username/password/department match exactly |

---

## 📁 Important Files

| File          | Purpose                          |
|---------------|----------------------------------|
| main.py       | Main server (FastAPI)            |
| database.py   | MySQL connection setup           |
| db_utils.py   | All database operations          |
| nlp.py        | AI intent detection (Gemini)     |
| requirements.txt | Python packages to install    |
| static/       | CSS, JS, images                  |
| templates/    | HTML pages                       |

---

## 🛑 To Stop the Server
Press `Ctrl + C` in the terminal

---

## 📱 OTP Setup (First Time)
1. Go to http://localhost:5000/setup
2. Enter master password: Admin@123
3. Click "Generate QR" for each user
4. Scan QR with Microsoft/Google Authenticator
5. Use the 6-digit code shown in the app to login

---

**App Name**: Smart DEO
**Tech Stack**: FastAPI + MySQL + Google Gemini AI
**Port**: 5000
