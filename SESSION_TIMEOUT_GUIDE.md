# Session Timeout Configuration Guide

## Overview
The Smart DEO application includes configurable session timeout to automatically log out inactive users for security.

## Current Configuration

### Default Settings
- **Timeout Duration**: 15 minutes (configurable)
- **Visual Timer**: Countdown displayed in sidebar
- **Auto-Logout**: Automatic redirect to login on expiration
- **Activity Tracking**: Updates on user interactions

## How to Configure

### Method 1: Environment Variable (Recommended)

Edit your `.env` file:

```bash
# Session Timeout (in minutes)
SESSION_TIMEOUT=15
```

Change `15` to your desired timeout in minutes.

### Method 2: Direct Code Edit

Edit `main.py` line 20:

```python
SESSION_TIMEOUT_MINUTES = int(os.environ.get('SESSION_TIMEOUT', 15))
```

Change the default `15` to your desired value.

## Recommended Timeout Values

### By Role

| Role  | Recommended | Reason |
|-------|-------------|--------|
| Admin | 30-60 min   | Frequent data entry, longer tasks |
| DEO   | 30-60 min   | Data management requires time |
| HOD   | 15-30 min   | Mostly viewing reports |

### By Environment

| Environment | Recommended | Reason |
|-------------|-------------|--------|
| Production  | 15 min      | Balanced security and usability |
| Development | 60 min      | Avoid frequent re-login during testing |
| Public PC   | 5-10 min    | Enhanced security on shared devices |
| Private PC  | 30-60 min   | More convenience for trusted devices |

### By Security Level

| Security Level | Timeout | Use Case |
|----------------|---------|----------|
| High Security  | 5 min   | Sensitive data, compliance requirements |
| Standard       | 15 min  | Normal office environment |
| Convenience    | 30 min  | Trusted users, private devices |
| Development    | 60 min  | Testing and development |

## How It Works

### Session Lifecycle

1. **Login**: Session starts, timer begins
2. **Activity**: User interacts with the application
3. **Update**: Last activity timestamp updated
4. **Idle**: User stops interacting
5. **Warning**: Timer counts down in sidebar
6. **Expiration**: Session expires after timeout
7. **Logout**: Automatic redirect to login page

### What Counts as Activity

**Updates Session:**
- Clicking navigation links
- Submitting forms
- Sending chat queries
- Uploading files
- Any page navigation

**Does NOT Update Session:**
- API calls for data refresh
- Background keepalive pings
- Reading static content
- Viewing current page

## Visual Indicators

### Sidebar Timer

The session timer is displayed in the sidebar:

```
⏱ 14:32  ← Time remaining
```

**Color Coding:**
- **Green** (>10 min): Session healthy
- **Yellow** (5-10 min): Warning
- **Red** (<5 min): About to expire

### Timer Updates

- Updates every second
- Shows minutes:seconds format
- Visible on all pages
- Synchronized with server

## Troubleshooting

### Issue: Session Expires Too Quickly

**Symptoms:**
- Logged out after a few minutes
- Timer shows less time than expected

**Solutions:**
1. Increase `SESSION_TIMEOUT` in `.env`
2. Restart the application
3. Clear browser cache
4. Check system clock is correct

**Example:**
```bash
# Change from 15 to 30 minutes
SESSION_TIMEOUT=30
```

### Issue: Session Never Expires

**Symptoms:**
- Timer doesn't count down
- Can stay logged in indefinitely

**Solutions:**
1. Check `SESSION_TIMEOUT` is set correctly
2. Verify middleware is configured
3. Clear browser cookies
4. Restart application

### Issue: Timer Not Visible

**Symptoms:**
- No timer in sidebar
- Timer shows "⏱ --:--"

**Solutions:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Check JavaScript console for errors
3. Verify `static/script.js` is loaded
4. Clear browser cache

### Issue: Logged Out While Active

**Symptoms:**
- Logged out while actively using
- Timer resets unexpectedly

**Solutions:**
1. Check network connection
2. Verify server is running
3. Check for JavaScript errors
4. Increase timeout value

## Security Best Practices

### General Guidelines

1. **Balance Security and Usability**
   - Too short: Frustrating for users
   - Too long: Security risk

2. **Consider Environment**
   - Public computers: Shorter timeout
   - Private offices: Longer timeout

3. **Role-Based Timeouts**
   - Admins: Longer (more tasks)
   - Viewers: Shorter (less interaction)

4. **Monitor and Adjust**
   - Track user feedback
   - Adjust based on usage patterns

### Compliance Requirements

**GDPR/Data Protection:**
- Recommended: 15 minutes
- Maximum: 30 minutes
- Justification: Minimize unauthorized access

**PCI DSS (if handling payments):**
- Required: 15 minutes maximum
- Recommended: 10 minutes

**HIPAA (if handling health data):**
- Required: 15 minutes maximum
- Recommended: 10 minutes

**General Business:**
- Recommended: 15-30 minutes
- Adjust based on risk assessment

## Advanced Configuration

### Per-Role Timeouts (Future Enhancement)

Currently, all roles share the same timeout. To implement per-role timeouts:

```python
# In main.py
ROLE_TIMEOUTS = {
    'Admin': 60,  # 60 minutes
    'DEO': 45,    # 45 minutes
    'HOD': 30     # 30 minutes
}

def require_login(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get role-specific timeout
    role = user.get('role', 'HOD')
    timeout_minutes = ROLE_TIMEOUTS.get(role, 15)
    
    # Check expiration
    last = request.session.get('last_active')
    if last:
        elapsed = datetime.utcnow() - datetime.fromisoformat(last)
        if elapsed > timedelta(minutes=timeout_minutes):
            request.session.clear()
            raise HTTPException(status_code=401, detail="Session expired")
    
    request.session['last_active'] = datetime.utcnow().isoformat()
    return user
```

### Idle Warning (Future Enhancement)

Show a warning popup before session expires:

```javascript
// In static/script.js
function checkSessionExpiry() {
    const remaining = getTimeRemaining();
    
    if (remaining < 60 && !warningShown) {
        showWarning('Your session will expire in 1 minute. Click to stay logged in.');
        warningShown = true;
    }
}

function showWarning(message) {
    if (confirm(message)) {
        // Send keepalive request
        fetch('/api/keepalive', { method: 'POST' });
        warningShown = false;
    }
}
```

### Remember Me (Future Enhancement)

Allow users to extend their session:

```html
<!-- In login.html -->
<label>
    <input type="checkbox" name="remember" value="1">
    Remember me for 7 days
</label>
```

```python
# In main.py
@app.post("/login")
async def login(request: Request):
    # ... existing login code ...
    
    remember = data.get('remember', False)
    if remember:
        # Extend session to 7 days
        request.session['max_age'] = 7 * 24 * 60 * 60
    
    return JSONResponse({'success': True})
```

## Testing

### Manual Testing

1. **Login**: Log in to the application
2. **Wait**: Wait for timeout duration
3. **Verify**: Check if logged out automatically
4. **Timer**: Verify countdown is accurate

### Automated Testing

```python
# test_session_timeout.py
import time
from datetime import datetime, timedelta

def test_session_timeout():
    # Login
    response = client.post('/login', json={
        'username': 'test_user',
        'password': 'test_pass',
        'otp': '123456'
    })
    assert response.json()['success']
    
    # Wait for timeout + 1 minute
    time.sleep((SESSION_TIMEOUT_MINUTES + 1) * 60)
    
    # Try to access protected route
    response = client.get('/chat')
    assert response.status_code == 401  # Should be logged out
```

## Quick Reference

### Configuration File
```bash
# .env
SESSION_TIMEOUT=15
```

### Restart Application
```bash
# Stop current process (Ctrl+C)
# Then restart:
python main.py
# or
uvicorn main:app --reload
```

### Check Current Timeout
```python
# In Python console
import os
print(f"Current timeout: {os.environ.get('SESSION_TIMEOUT', 15)} minutes")
```

### Common Values
- **5 minutes**: High security
- **10 minutes**: Compliance (PCI DSS, HIPAA)
- **15 minutes**: Standard (recommended)
- **30 minutes**: Convenience
- **60 minutes**: Development

## Support

For issues or questions:
1. Check this guide first
2. Verify `.env` configuration
3. Restart application after changes
4. Clear browser cache
5. Check JavaScript console for errors

## Related Documentation

- `EMAIL_NOTIFICATION_GUIDE.md` - Email notification setup
- `CONSOLE_GUIDE.md` - Console page usage
- `HOW_TO_START.md` - Application startup guide
