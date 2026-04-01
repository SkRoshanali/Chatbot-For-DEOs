# Fixes Applied

## 1. Excel/CSV/PDF Upload Not Working

**Root Cause**: MongoDB might not be running or connection issues.

**Fixes Applied**:
- Added MongoDB connection test at startup with error messages
- Added debug print statements in upload route to track file processing
- Added `/api/dbstatus` endpoint to check DB connection from browser
- Created `start_mongodb.bat` to help start MongoDB service
- Created `test_upload.py` to verify MongoDB and create test data

**How to Debug**:
1. Run `python test_upload.py` to check if MongoDB is accessible
2. If MongoDB is not running, run `start_mongodb.bat`
3. Check Flask console for `[UPLOAD]` messages when uploading
4. Visit `http://127.0.0.1:5000/api/dbstatus` (after login) to check DB status

**Expected Console Output on Upload**:
```
[UPLOAD] Received file: students.xlsx
[UPLOAD] Inserted: 5, Updated: 0, Skipped: 0
```

---

## 2. Session Timer Fluctuating

**Root Cause**: 
- Timer was resetting on every mouse move/activity
- `/api/me` calls were updating `last_active` causing timer jumps

**Fixes Applied**:
- Removed `mousemove` and `touchstart` from activity listeners (too frequent)
- Only track `click` and `keydown` for activity
- Excluded `/api/me` from updating `last_active` timestamp
- Added throttling: server only gets keepalive ping every 30 seconds max
- Timer now counts down smoothly without jumps

**Behavior Now**:
- Timer starts at 15:00 on page load
- Counts down every second
- Resets to 15:00 when you click or type
- Turns red when under 2 minutes
- Auto-logout at 0:00

---

## 3. Refresh Count Increased

**Changed**: Refresh limit increased from 5 to 20 page refreshes

**Location**: `chatbot/app.py` line ~44
```python
if refresh_count >= 20:  # Increased from 5 to 20
```

**Note**: Only actual page navigations count (not API calls or data operations)

---

## 4. Login Icons Removed

**Changed**: All SVG icons removed from login form inputs

**Reason**: Icons were overlapping with placeholder text and causing visual clutter

**Files Modified**:
- `chatbot/templates/login.html` - removed all `<span class="input-icon">` elements
- `chatbot/static/style.css` - simplified input styling, removed icon positioning

**Result**: Clean, simple input fields with no visual conflicts

---

## Testing Checklist

### Upload Test:
1. ✅ Run `python test_upload.py`
2. ✅ Start Flask: `python chatbot/app.py`
3. ✅ Login as `deo_cse` / `cse123`
4. ✅ Go to Data Management → Upload File
5. ✅ Upload `test_upload.xlsx` (created by test script)
6. ✅ Check View Data tab for TEST001 and TEST002
7. ✅ Check Flask console for `[UPLOAD]` messages

### Timer Test:
1. ✅ Login and go to chat page
2. ✅ Watch timer in sidebar footer
3. ✅ Verify it counts down smoothly (15:00 → 14:59 → 14:58...)
4. ✅ Click anywhere → timer resets to 15:00
5. ✅ Wait 2 minutes without activity → timer should be at 13:00
6. ✅ No jumping or fluctuation

### Refresh Test:
1. ✅ Login
2. ✅ Press F5 (refresh) 20 times
3. ✅ On 21st refresh → should logout with "too many refreshes" message
4. ✅ Chatting and uploading files should NOT count toward refresh limit

---

## MongoDB Installation (if needed)

If MongoDB is not installed:

1. Download: https://www.mongodb.com/try/download/community
2. Install with default settings
3. MongoDB should auto-start as a Windows service
4. If not, run `start_mongodb.bat`

Or use MongoDB Compass (GUI) to verify connection:
- Download: https://www.mongodb.com/try/download/compass
- Connect to: `mongodb://localhost:27017`
- Check database: `deo_chatbot`
- Check collection: `students`
