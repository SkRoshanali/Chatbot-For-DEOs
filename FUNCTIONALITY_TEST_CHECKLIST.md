# ✅ Functionality Test Checklist

## 🔐 1. Login & Authentication

### Test Login:
- [ ] Open http://localhost:5000/login
- [ ] Enter username: `deo_cse`
- [ ] Enter password: `cse123`
- [ ] Select department: `CSE`
- [ ] Enter OTP from Microsoft Authenticator
- [ ] Click "Sign In"
- [ ] ✅ Should redirect to `/chat`

### Test Theme Toggle on Login Page:
- [ ] Look for 🌙 button in top-right corner
- [ ] Click to switch to dark mode
- [ ] Click ☀️ to switch back to light mode
- [ ] ✅ Theme should change smoothly

---

## 💬 2. Chat/Chatbot Interface

### Check Chat Page Layout:
- [ ] After login, you should see:
  - [ ] Left sidebar with quick report buttons
  - [ ] Main chat area in the center
  - [ ] Welcome message from bot
  - [ ] Input box at the bottom
  - [ ] Session timer in sidebar: `⏱ 15:00`

### Test Sidebar (Fixed Position):
- [ ] Scroll down in the chat messages
- [ ] ✅ Sidebar should stay fixed (not scroll)
- [ ] ✅ Session timer should always be visible

### Test Session Timer:
- [ ] Look at sidebar footer
- [ ] ✅ Should see: `⏱ 15:00` (or current time)
- [ ] Wait 10 seconds
- [ ] ✅ Timer should count down: `⏱ 14:50`
- [ ] Click anywhere on the page
- [ ] ✅ Timer should reset to `⏱ 15:00`

### Test Quick Report Buttons:
- [ ] Click "Student by Roll No" button
- [ ] ✅ Should send query to chatbot
- [ ] ✅ Bot should respond with student data
- [ ] Try other buttons:
  - [ ] "Section 1 Students"
  - [ ] "Section-wise attendance"
  - [ ] "Low Attendance"
  - [ ] "Internal Marks"
  - [ ] "Backlog List"
  - [ ] "CGPA Distribution"

### Test Manual Chat Input:
- [ ] Type in input box: `show attendance for section 1`
- [ ] Press Enter or click "Send"
- [ ] ✅ Message should appear in chat
- [ ] ✅ Bot should respond with data

### Test Chat Queries:
Try these queries:
- [ ] `show students in section 1`
- [ ] `show attendance for CSE`
- [ ] `show students with low attendance`
- [ ] `show top performers`
- [ ] `show students with backlogs`
- [ ] `show CGPA distribution`
- [ ] `show average marks`

### Test Export Functionality:
- [ ] After getting a report, look for export bar
- [ ] ✅ Should see: 📄 CSV | 📊 Excel | 🖨️ PDF buttons
- [ ] Click "📄 CSV"
- [ ] ✅ Should download CSV file
- [ ] Click "📊 Excel"
- [ ] ✅ Should download Excel file

---

## 📂 3. Data Management

### Navigate to Data Management:
- [ ] Click "📂 Data Management" in sidebar
- [ ] ✅ Should navigate to `/data`

### Check Data Management Layout:
- [ ] Should see three tabs:
  - [ ] ✏️ Manual Entry
  - [ ] 📤 Upload File
  - [ ] 📋 View Data

### Test Sidebar (Fixed Position):
- [ ] Click "✏️ Manual Entry" tab
- [ ] Scroll down the form
- [ ] ✅ Sidebar should stay fixed (not scroll)
- [ ] ✅ Session timer should always be visible

### Test Session Timer:
- [ ] Look at sidebar footer
- [ ] ✅ Should see: `⏱ 15:00` (or current time)
- [ ] ✅ Timer should count down every second

### Test Manual Entry Tab:
- [ ] Fill in student details:
  - [ ] Roll Number: `TEST001`
  - [ ] Name: `Test Student`
  - [ ] Department: `CSE`
  - [ ] Section: `SEC-1`
  - [ ] Joining Year: `2023`
  - [ ] Attendance: `85`
  - [ ] Internal: `42`
  - [ ] External: `70`
- [ ] ✅ Semester and Batch should auto-fill
- [ ] ✅ CGPA should auto-calculate
- [ ] Click "➕ Add Student"
- [ ] ✅ Should show success message

### Test View Data Tab:
- [ ] Click "📋 View Data" tab
- [ ] ✅ Should see table with all students
- [ ] ✅ Table should be horizontal (not vertical)
- [ ] ✅ Should see color badges:
  - 🟢 Green for good performance
  - 🟡 Yellow for average
  - 🔴 Red for poor performance

### Test Table Features:
- [ ] ✅ Table header should be sticky (stays visible when scrolling)
- [ ] ✅ All columns should be visible without horizontal scroll
- [ ] Hover over a row
- [ ] ✅ Row should highlight
- [ ] Try search box
- [ ] Type a student name
- [ ] ✅ Table should filter results

### Test Edit Student:
- [ ] Click ✏️ Edit button on any student
- [ ] ✅ Should switch to Manual Entry tab
- [ ] ✅ Form should be filled with student data
- [ ] Change some values
- [ ] Click "💾 Update Student"
- [ ] ✅ Should show success message
- [ ] Go back to View Data tab
- [ ] ✅ Changes should be reflected

### Test Delete Student:
- [ ] Click 🗑️ Delete button on test student
- [ ] ✅ Should ask for confirmation
- [ ] Confirm deletion
- [ ] ✅ Student should be removed from table

### Test Upload File Tab:
- [ ] Click "📤 Upload File" tab
- [ ] ✅ Should see upload zone
- [ ] ✅ Should see "Download Excel Template" button
- [ ] Click "Download Excel Template"
- [ ] ✅ Should download template file

### Test Refresh Button:
- [ ] In View Data tab, click 🔄 Refresh
- [ ] ✅ Table should reload
- [ ] ✅ Should show latest data

---

## 🎨 4. Theme Toggle

### Test on All Pages:
- [ ] Login page: Click 🌙/☀️
- [ ] Chat page: Click 🌙/☀️
- [ ] Data Management: Click 🌙/☀️
- [ ] ✅ Theme should change on all pages

### Test Light Mode:
- [ ] Switch to light mode (🌙)
- [ ] ✅ Should see:
  - Blue gradient sidebar
  - White background
  - Blue gradient buttons
  - Blue gradient table headers
  - Professional color scheme

### Test Dark Mode:
- [ ] Switch to dark mode (☀️)
- [ ] ✅ Should see:
  - Dark gradient sidebar
  - Dark navy background
  - Dark buttons with glow
  - Dark table headers
  - Easy on eyes

### Test Theme Persistence:
- [ ] Switch to dark mode
- [ ] Refresh the page (F5)
- [ ] ✅ Should stay in dark mode
- [ ] Close browser and reopen
- [ ] ✅ Should remember your theme choice

---

## 🔄 5. Session Management

### Test Session Timer:
- [ ] Login and note the timer
- [ ] Wait 1 minute
- [ ] ✅ Timer should show `⏱ 14:00`
- [ ] Click anywhere
- [ ] ✅ Timer should reset to `⏱ 15:00`

### Test Session Expiry Warning:
- [ ] Wait until timer shows < 2 minutes
- [ ] ✅ Timer should turn red
- [ ] ✅ Should show warning color

### Test Auto Logout:
- [ ] Wait until timer reaches `⏱ 0:00`
- [ ] ✅ Should automatically logout
- [ ] ✅ Should redirect to login page

### Test Manual Logout:
- [ ] Click "Logout" button in sidebar
- [ ] ✅ Should logout immediately
- [ ] ✅ Should redirect to login page

---

## 📱 6. Responsive Design

### Test on Different Screen Sizes:
- [ ] Desktop (>1024px):
  - [ ] Sidebar visible on left
  - [ ] Content on right
  - [ ] All features accessible
- [ ] Tablet (768px-1024px):
  - [ ] Sidebar hidden by default
  - [ ] Content full width
  - [ ] Menu button to open sidebar
- [ ] Mobile (<768px):
  - [ ] Compact layout
  - [ ] Touch-friendly buttons
  - [ ] Scrollable content

---

## 🐛 7. Error Handling

### Test Invalid Login:
- [ ] Enter wrong username
- [ ] ✅ Should show error message
- [ ] Enter wrong password
- [ ] ✅ Should show error message
- [ ] Enter wrong OTP
- [ ] ✅ Should show "Invalid OTP" message

### Test Empty Form Submission:
- [ ] In Manual Entry, click "Add Student" without filling form
- [ ] ✅ Should show validation errors

### Test Network Errors:
- [ ] Stop the server
- [ ] Try to send a chat message
- [ ] ✅ Should show error message
- [ ] Restart server
- [ ] ✅ Should work again

---

## ✅ Summary Checklist

### Core Functionality:
- [ ] ✅ Login works with Microsoft Authenticator
- [ ] ✅ Chat interface visible and working
- [ ] ✅ Chatbot responds to queries
- [ ] ✅ Quick report buttons work
- [ ] ✅ Data management works
- [ ] ✅ Manual entry works
- [ ] ✅ View data table works
- [ ] ✅ Edit/Delete works
- [ ] ✅ Upload file works

### UI/UX:
- [ ] ✅ Sidebar stays fixed when scrolling
- [ ] ✅ Session timer visible and counting down
- [ ] ✅ Light theme looks professional
- [ ] ✅ Dark theme looks modern
- [ ] ✅ Theme toggle works on all pages
- [ ] ✅ Hover effects smooth
- [ ] ✅ Transitions smooth
- [ ] ✅ Color badges visible

### Session Management:
- [ ] ✅ Timer counts down from 15:00
- [ ] ✅ Timer resets on activity
- [ ] ✅ Timer turns red when < 2 minutes
- [ ] ✅ Auto logout at 0:00
- [ ] ✅ Manual logout works

---

## 🎯 Quick Test (5 Minutes):

1. **Login** → Enter credentials + OTP
2. **Check Chat** → Send a query, get response
3. **Check Sidebar** → Scroll, sidebar stays fixed
4. **Check Timer** → See `⏱ 15:00` counting down
5. **Toggle Theme** → Click 🌙, see light mode
6. **Data Management** → View table, see data
7. **Scroll Form** → Sidebar stays fixed
8. **Logout** → Click logout button

If all 8 steps work → ✅ Everything is working!

---

## 🆘 Troubleshooting:

### Chat not visible?
- Hard refresh: Ctrl + Shift + R
- Check browser console (F12) for errors
- Check if logged in correctly

### Sidebar scrolling?
- Hard refresh the page
- Clear browser cache
- Check if modern-style.css loaded

### Timer not showing?
- Check sidebar footer
- Hard refresh the page
- Check browser console for errors

### Theme not changing?
- Click the 🌙/☀️ button in top-right
- Hard refresh after clicking
- Check if theme-toggle.js loaded

---

## ✅ Expected Results:

After completing all tests, you should have:
- ✅ Working login with Microsoft Authenticator
- ✅ Functional chatbot interface
- ✅ Fixed sidebar that doesn't scroll
- ✅ Visible session timer counting down
- ✅ Beautiful light and dark themes
- ✅ Working data management
- ✅ Smooth user experience

**Everything should be working perfectly!** 🎉
