# Phishing Detection Extension - Windows Troubleshooting Guide

This guide covers common issues and solutions for Windows users setting up the extension.

---

## Pre-Flight Checklist

Run this checklist before debugging:

- [ ] Python installed (`python --version` in CMD shows version)
- [ ] Flask installed (`pip show flask` returns results)
- [ ] flask-cors installed (`pip show flask-cors` returns results)
- [ ] Port 5000 is available (see "Port 5000 Already in Use" section)
- [ ] No firewall blocking localhost:5000
- [ ] Chrome/Chromium based browser updated to latest version
- [ ] Extension files in correct folder (`extension/manifest.json` exists)

---

## Issue 1: Python Not Found / 'python' is not recognized

**Error Message:**
```
'python' is not recognized as an internal or external command,
operable program or batch file.
```

**Solution:**

1. **Check if Python is installed:**
   - Open Command Prompt (Win+R, type `cmd`, press Enter)
   - Type: `python --version`
   - If this fails, Python is not installed

2. **Install Python:**
   - Go to https://www.python.org/downloads/
   - Download Python 3.9 or higher
   - **IMPORTANT:** During installation, CHECK the box "Add Python to PATH"
   - Click "Install Now"

3. **Verify installation:**
   - Close and reopen Command Prompt
   - Type: `python --version`
   - Should show: `Python 3.x.x`

4. **Try alternative command:**
   - Some systems use `python3` instead of `python`
   - Try: `python3 --version`
   - If this works, use `python3` instead of `python` in all commands

**If still not working:**
- Uninstall Python completely
- Restart Windows
- Reinstall with PATH checkbox checked

---

## Issue 2: Flask Not Installed

**Error Message:**
```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**

1. **Install Flask:**
   ```bash
   pip install flask flask-cors
   ```

2. **Verify installation:**
   ```bash
   pip show flask
   pip show flask-cors
   ```

3. **If pip command not found:**
   - Try: `python -m pip install flask flask-cors`

4. **If still failing:**
   - Uninstall Flask: `pip uninstall flask flask-cors`
   - Clear pip cache: `pip cache purge`
   - Reinstall: `pip install flask flask-cors`

---

## Issue 3: Port 5000 Already in Use

**Error Message:**
```
Address already in use
OSError: [WinError 10048] Only one usage of each socket address...
Port 5000 is already in use by another process
```

**Solution:**

1. **Find what's using port 5000:**
   ```bash
   netstat -ano | findstr :5000
   ```
   - Note the PID number

2. **Stop the process (two options):**

   **Option A - Task Manager (easiest):**
   - Press Ctrl+Shift+Esc to open Task Manager
   - Find the process using the PID from step 1
   - Right-click → End Task

   **Option B - Command Line:**
   ```bash
   taskkill /PID <process_id> /F
   ```
   Replace `<process_id>` with the number from step 1

3. **Change the port (alternative):**
   - Open `flask_server.py`
   - Find line: `app.run(debug=True, host='localhost', port=5000)`
   - Change to: `app.run(debug=True, host='localhost', port=5001)`
   - Update content.js and popup.js to use port 5001

---

## Issue 4: Flask Server Starts But Immediately Closes

**Error Message:**
- Window appears and closes immediately

**Solution:**

1. **Run using batch file instead:**
   - Double-click `RUN_EXTENSION_SERVER.bat`
   - Should stay open if successful

2. **Check for Python syntax errors:**
   ```bash
   python -m py_compile flask_server.py
   ```
   - If it fails, there's a syntax error in the file

3. **Run with verbose output:**
   ```bash
   python -u flask_server.py
   ```
   - `-u` forces unbuffered output

4. **Check if dependencies are missing:**
   - Do you have all required files?
   - `predict.py`, `feature_extractor.py`, `semantic_detector.py`, `model.pkl`
   - If any are missing, the server cannot start

---

## Issue 5: Extension Not Loading

**Error Message:**
- Extension doesn't appear in `chrome://extensions/`
- Error like "Failed to load extension"

**Solution:**

1. **Check folder structure:**
   ```
   extension/
   ├── manifest.json
   ├── background.js
   ├── content.js
   ├── popup.html
   ├── popup.js
   └── icons/
       └── icon-16.svg
   ```
   - All these files must exist in `extension/` folder

2. **Load extension manually:**
   - Open Chrome
   - Paste in address bar: `chrome://extensions/`
   - Enable "Developer mode" (top-right toggle)
   - Click "Load unpacked"
   - Select the `extension/` folder (NOT the parent folder)

3. **Check manifest.json:**
   - Open `extension/manifest.json`
   - Look for syntax errors (red squiggles in VS Code)
   - Ensure all quotes match: `"key": "value"`

4. **Clear Chrome cache:**
   - Go to `chrome://extensions/`
   - Disable extension, then enable
   - Or: Remove extension, restart Chrome, reload

---

## Issue 6: Extension Loaded But Not Working

**Error Message:**
- Extension appears in chrome://extensions/ but doesn't show warnings
- Links open without being analyzed

**Solution:**

1. **Check Flask server is running:**
   - Open Command Prompt
   - Type: `curl http://localhost:5000/health` (or use browser)
   - Should show green checkmark and JSON response
   - If it fails, Flask server isn't running

2. **Check Chrome DevTools Console:**
   - Press F12 on any webpage
   - Go to "Console" tab
   - Look for error messages starting with `[Phishing Detector]`
   - Common errors:
     - "Failed to fetch from Flask": Server not running
     - "Content script not loaded": Extension not reloaded

3. **Reload the extension:**
   - Go to `chrome://extensions/`
   - Find "🔒 Phishing Link Detector"
   - Click the refresh icon
   - Reload webpage (F5)

4. **Test with our test script:**
   - Run: `python test_extension_backend.py`
   - Should show "all tests passed"
   - If it fails, Flask server has issues

---

## Issue 7: "ERR_CONNECTION_REFUSED" when Flask tries to connect

**Error Message:**
```
[Phishing Detector] Failed to fetch from Flask API
ERR_CONNECTION_REFUSED
```

**Solution:**

1. **Verify Flask is running:**
   ```bash
   curl http://localhost:5000/health
   ```
   - Should respond with JSON
   - If "Connection refused", server isn't running

2. **Start Flask server:**
   - Open Command Prompt in project folder
   - Type: `python flask_server.py`
   - Should show: "Running on http://localhost:5000/"

3. **Check firewall settings:**
   - Windows Defender might block localhost connections
   - Open Windows Defender Firewall
   - Click "Allow an app through firewall"
   - Make sure "Python" is checked for Private networks

4. **Check content.js configuration:**
   - Open `extension/content.js`
   - Find line: `const API_URL = 'http://localhost:5000/predict';`
   - Make sure it matches your Flask port

---

## Issue 8: Extension Shows "Server Unavailable"

**Symptom:**
- Popup shows warning icon with "Flask server not responding"

**Solution:**

1. **Start Flask server:**
   ```bash
   python flask_server.py
   ```

2. **Test connection:**
   ```bash
   curl http://localhost:5000/health
   ```

3. **Check if port changed:**
   - If you changed from port 5000, update all references:
     - `extension/content.js` (search for "localhost:5000")
     - `extension/popup.js` (search for "localhost:5000")

4. **Check CORS configuration:**
   - Open `flask_server.py`
   - Line should have: `CORS(app)`
   - If missing, extension cannot communicate with Flask

---

## Issue 9: Modal Doesn't Appear When Clicking Links

**Symptom:**
- Links open normally without any warning modal
- Even for known phishing URLs

**Solution:**

1. **Check content.js loaded:**
   - Press F12 on any webpage
   - Go to "Sources" tab
   - Look for `content.js` in left panel
   - If not there, extension not loaded properly

2. **Check console for errors:**
   - Press F12
   - Go to "Console" tab
   - Should show: `[Phishing Detector] Content script loaded`
   - If error appears, there's an issue in content.js

3. **Check URL format:**
   - Modal only appears if URL starts with `http://` or `https://`
   - Links like `#anchor`, `javascript:`, `mailto:` are ignored
   - This is intentional for safety

4. **Lower sensitivity threshold:**
   - Open `extension/content.js`
   - Find: `const MIN_PHISHING_CONFIDENCE = 0.6;`
   - Change to: `const MIN_PHISHING_CONFIDENCE = 0.5;`
   - Reload extension (chrome://extensions/)

---

## Issue 10: Too Many False Positives

**Symptom:**
- Legitimate websites trigger warnings
- Always shows red alert modal

**Solution:**

1. **Increase confidence threshold:**
   - Open `extension/content.js`
   - Find: `const MIN_PHISHING_CONFIDENCE = 0.6;`
   - Change to: `const MIN_PHISHING_CONFIDENCE = 0.8;`
   - Now only high-confidence predictions trigger warnings

2. **Test the adjustment:**
   - Go to a legitimate website (e.g., google.com)
   - Click several links
   - Should open without warnings
   - Try suspicious URLs to verify they still trigger warnings

3. **Check Flask model accuracy:**
   - Run: `python test_extension_backend.py`
   - Look at test results
   - If accuracy is low, the ML model needs retraining

---

## Issue 11: Extension Crashes / Pages Become Unresponsive

**Symptom:**
- Websites freeze or become very slow with extension enabled
- Chrome uses excessive CPU/RAM

**Solution:**

1. **Disable link caching (very aggressive approach):**
   - Open `extension/content.js`
   - Find: `const analyzedUrls = new Set();`
   - Comment it out partially to reduce per-session memory

2. **Increase API call timeout:**
   - Open `extension/background.js`
   - Find: `fetch(..., {timeout: 10000})`
   - Increase timeout: `{timeout: 20000}`
   - This gives slower connections more time

3. **Disable for certain domains:**
   - Open `extension/content.js`
   - Add domain whitelist:
   ```javascript
   const WHITELIST_DOMAINS = ['gmail.com', 'github.com'];
   if (WHITELIST_DOMAINS.some(d => location.hostname.includes(d))) return;
   ```

4. **Check Flask server performance:**
   - Run: `python test_extension_backend.py`
   - Watch how fast predictions return
   - If slow (>5 seconds), optimize Flask server

---

## Issue 12: Can't Edit Extension Files

**Symptom:**
- Files are read-only or locked
- Cannot save changes to manifest.json

**Solution:**

1. **Check file permissions:**
   - Right-click file → Properties
   - Go to "Security" tab
   - Click "Edit"
   - Select your user account
   - Check "Full Control"
   - Click "Apply"

2. **Close Chrome first:**
   - Chrome locks extension files while running
   - Close Chrome completely
   - Edit the files
   - Reopen Chrome and reload extension

3. **Use VS Code to edit:**
   - Right-click `extension/` folder
   - Select "Open with Code"
   - VS Code typically has better file handling

---

## Issue 13: Flask Shows "Address in use" on Restart

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**

1. **Kill old Flask process:**
   ```bash
   netstat -ano | findstr :5000
   taskkill /PID <pid> /F
   ```

2. **Wait before restarting:**
   - Wait 10 seconds after stopping Flask
   - Then start it again

3. **Use different port:**
   - Edit `flask_server.py` last line
   - Change: `app.run(port=5000)` → `app.run(port=5001)`

---

## Debugging Tips

### Enable Detailed Logging

1. **In Flask server:**
   - `flask_server.py` already has `debug=True`
   - Shows all API calls in console

2. **In Chrome Extension:**
   - Press F12 → Console tab
   - Shows all content script messages
   - Look for `[Phishing Detector]` messages

3. **Enable Flask verbose logging:**
   ```python
   # In flask_server.py, add at top:
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Test Individual Components

**Test Flask directly (without extension):**
```bash
curl -X POST http://localhost:5000/predict -H "Content-Type: application/json" -d "{\"url\": \"https://example.com\"}"
```

**Test Extension without Flask:**
- Load extension in Chrome
- Open DevTools (F12)
- Go to Console
- Extension still loads but shows "Server unavailable" - that's OK

### Collect Error Information

When reporting issues, collect:
1. Output from: `python test_extension_backend.py`
2. Chrome DevTools Console (F12 → Console tab)
3. Flask Server terminal output
4. Windows Event Viewer error logs (if applicable)

---

## Getting Help

If these steps don't work:

1. **Check the logs:**
   - Flask server terminal window for error messages
   - Chrome DevTools Console (F12) for JavaScript errors

2. **Review the main guides:**
   - [EXTENSION_SETUP.md](EXTENSION_SETUP.md) - Full setup guide
   - [QUICK_START_EXTENSION.md](QUICK_START_EXTENSION.md) - 5-minute guide

3. **Verify file structure:**
   ```bash
   # Run in project folder
   dir extension
   ```
   Should show all required files

4. **Test backend:**
   ```bash
   python test_extension_backend.py
   ```
   All tests should pass

---

## Quick Fix Checklist

Try this order when something stops working:

1. [ ] Restart Chrome (close completely, reopen)
2. [ ] Restart Flask server (Ctrl+C, start fresh)
3. [ ] Reload extension (chrome://extensions/ → refresh icon)
4. [ ] Clear Chrome cache (Settings → Privacy → Clear browsing data)
5. [ ] Reinstall Flask: `pip uninstall flask && pip install flask flask-cors`
6. [ ] Run test script: `python test_extension_backend.py`
7. [ ] Check Windows firewall (allow Python)
8. [ ] Unload and reload extension from scratch

---

## Contact Information

If issues persist after following this guide:

1. Check that all files exist:
   - `flask_server.py`, `predict.py`, `feature_extractor.py`
   - `extension/manifest.json` and friends
   - `model/model.pkl`

2. Verify Python 3.8+ is installed

3. Run diagnostic:
   ```bash
   python test_extension_backend.py
   ```

4. Share the output of that test with support

---

**Last Updated:** January 2024
**Tested On:** Windows 10, Windows 11  
**Python Version:** 3.8+
**Chrome Version:** 120+
