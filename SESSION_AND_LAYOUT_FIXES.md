# Session Timer & Bot Message Layout Fixes

## Changes Made - Version 13.0

### 1. Session Timer - Strict 15 Minute Enforcement ✅

#### Issue:
- Session timer was working but needed stricter enforcement
- Navigating back to login page didn't immediately logout
- Timer should reset on ANY activity (already working correctly)

#### Solution:

**Auto-Logout on Login Page Navigation:**
```javascript
// If user navigates back to login page while logged in, logout immediately
if (isLoginPage) {
  fetch('/api/me', { credentials: 'same-origin' })
    .then(r => r.json())
    .then(data => {
      if (data && data.username) {
        // User is still logged in but on login page - logout
        fetch('/logout', { credentials: 'same-origin' })
          .then(() => {
            sessionStorage.clear();
            localStorage.clear();
          });
      }
    });
}
```

**How It Works:**
1. When login page loads, check if user is still logged in
2. If logged in, immediately call `/logout` endpoint
3. Clear all session and local storage
4. User must login again

**Timer Reset Behavior (Already Working):**
- Timer resets to 15 minutes on ANY activity:
  - Mouse clicks
  - Keyboard input
  - Scrolling
  - Navigation between chat/data management
  - Sending messages
  - Running queries
- Backend updates `last_active` timestamp on every request
- Frontend timer syncs with backend every 30 seconds

**Strict Enforcement:**
- Timer counts down from 15:00 to 0:00
- At 0:00, automatic redirect to `/logout`
- Timer turns red when < 2 minutes remaining
- No grace period - exactly 15 minutes

### 2. Bot Message Width - Neat Fit Layout ✅

#### Issue:
- Bot messages were taking full width (100%)
- Made output look cluttered and hard to read
- Tables and content stretched across entire screen

#### Solution:

**Message Width Limits:**
```css
/* Bot messages: 90% max width */
.bot-message .bubble {
  max-width: 90%;
}

/* User messages: 75% max width */
.user-message .bubble {
  max-width: 75%;
}

/* Base bubble: 85% max width */
.bubble {
  max-width: 85%;
}
```

**Table Handling Inside Messages:**
```css
/* Tables scroll horizontally if too wide */
.bot-message .bubble .report-table {
  max-width: 100%;
  overflow-x: auto;
  display: block;
}

/* Smaller font for tables in messages */
.bot-message .bubble table {
  max-width: 100%;
  font-size: 0.8rem;
}
```

**Overflow Handling:**
```css
/* Bot messages can scroll horizontally if needed */
.bot-message .bubble {
  overflow-x: auto;
  overflow-y: visible;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* Custom scrollbar for bot messages */
.bot-message .bubble::-webkit-scrollbar {
  height: 6px;
}
```

**Responsive Behavior:**
```css
/* Mobile: Allow more width (95%) */
@media (max-width: 640px) {
  .bubble {
    max-width: 95%;
  }
  
  .bot-message .bubble {
    max-width: 95%;
  }
  
  .user-message .bubble {
    max-width: 90%;
  }
}
```

## Visual Comparison

### Before (Full Width) ❌
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 Bot Message taking entire width of screen                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Table stretching across full width                          │ │
│ │ Hard to read, cluttered appearance                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### After (Neat Fit) ✅
```
┌─────────────────────────────────────────────────────────────────┐
│ 🤖 Bot Message fits neatly (90% width)                          │
│ ┌───────────────────────────────────────────────────┐           │
│ │ Table contained within message bubble             │           │
│ │ Clean, readable, professional appearance          │           │
│ └───────────────────────────────────────────────────┘           │
│                                                                  │
│                                    User Message (75%) 👤         │
│                          ┌──────────────────────────┐           │
│                          │ Shorter, right-aligned   │           │
│                          └──────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## Benefits

### Session Timer:
1. **Strict Security**: Exactly 15 minutes, no exceptions
2. **Auto-Logout**: Navigating back to login = immediate logout
3. **Activity Reset**: Any interaction resets timer to 15:00
4. **Visual Warning**: Red color when < 2 minutes remaining
5. **Clean State**: All storage cleared on logout

### Bot Message Layout:
1. **Better Readability**: Messages don't stretch across screen
2. **Professional Look**: Neat, contained appearance
3. **Easier Scanning**: Eye doesn't have to travel full width
4. **Table Handling**: Tables scroll if too wide, don't break layout
5. **Responsive**: Adapts to mobile/tablet screens
6. **Consistent**: All messages follow same width rules

## Technical Details

### Session Timer Files Modified:
- `chatbot/static/script.js` - Added auto-logout on login page

### Bot Layout Files Modified:
- `chatbot/static/modern-style.css` - Updated bubble widths and overflow handling
- `chatbot/templates/index.html` - CSS version v13.0
- `chatbot/templates/data.html` - CSS version v13.0

### CSS Properties Used:
- `max-width`: Limit message width
- `overflow-x: auto`: Horizontal scroll for wide content
- `word-wrap: break-word`: Break long words
- `overflow-wrap: break-word`: Wrap text properly
- Custom scrollbar styling for better UX

### Browser Compatibility:
- ✅ Chrome, Firefox, Edge, Safari (modern versions)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)
- ⚠️ IE11: Graceful degradation (no custom scrollbar)

## Testing Checklist

### Session Timer:
- [ ] Login and wait 15 minutes - should auto-logout
- [ ] Click/type during session - timer should reset to 15:00
- [ ] Navigate to data management - timer should reset
- [ ] Send a query - timer should reset
- [ ] Navigate back to login page - should logout immediately
- [ ] Timer should turn red at < 2 minutes

### Bot Message Width:
- [ ] Send query "show section 1 students" - message should be ~90% width
- [ ] Send query "average marks" - table should fit neatly
- [ ] Send query with long table - should scroll horizontally
- [ ] User messages should be ~75% width, right-aligned
- [ ] Test on mobile - messages should be ~95% width
- [ ] Test on tablet - messages should maintain proper width

## Cache Clearing

Users must clear cache to see changes:
1. Hard refresh: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
2. Clear browser cache completely
3. Use incognito/private mode for testing
4. Verify CSS version is v13.0 in page source

---

**Status**: ✅ Complete
**Version**: 13.0
**Date**: 2026-04-08
**Changes**: Session timer strict enforcement + Bot message neat fit layout
