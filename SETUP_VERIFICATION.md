# Phishing Detection Extension - Installation Verification Guide

## Pre-Installation Checklist

Before starting, ensure you have:

- [ ] Python 3.8 or higher
- [ ] pip (Python package manager)
- [ ] Chrome/Chromium-based browser (Edge, Brave, Opera also work)
- [ ] ~500MB free disk space
- [ ] Stable internet connection

---

## Step 1: Verify Python Installation

**Windows Command Prompt:**
```bash
python --version
```

**Expected output:**
```
Python 3.9.0
```

**If this fails:**
```bash
python3 --version
```

If neither work, see [WINDOWS_TROUBLESHOOTING.md](WINDOWS_TROUBLESHOOTING.md) - "Python Not Found" section.

---

## Step 2: Verify Required Files Exist

**Navigate to project folder and check for:**

```bash
# Navigate to project folder
cd "c:\4TH SEM\Hackathon\phishing-detection"

# List all files  
dir
```

**You should see these files:**

```
✓ predict.py                          (existing ML model predictions)
✓ feature_extractor.py                (existing feature extraction)
✓ semantic_detector.py                (existing semantic analysis)
✓ model/model.pkl                     (existing trained model)
✓ flask_server.py                     (NEW: backend API server)
✓ requirements.txt                    (UPDATED: with Flask)
✓ extension/                          (NEW: extension folder)
  ├── manifest.json                   (extension config)
  ├── background.js                   (service worker)
  ├── content.js                      (link monitoring)
  ├── popup.html                      (popup UI)
  ├── popup.js                        (popup logic)
  └── icons/icon-16.svg               (extension icon)
✓ RUN_EXTENSION_SERVER.bat            (NEW: batch to start server)
✓ TEST_EXTENSION_BACKEND.bat          (NEW: batch to test backend)
✓ test_extension_backend.py           (NEW: Python test script)
✓ QUICK_START_EXTENSION.md            (NEW: quick start guide)
✓ EXTENSION_SETUP.md                  (NEW: full setup guide)
✓ WINDOWS_TROUBLESHOOTING.md          (NEW: troubleshooting guide)
```

**Missing files?** Use the guides to create them or download again.

---

## Step 3: Install Python Dependencies

**Option A - Using batch file (recommended for Windows):**

Just double-click: `RUN_EXTENSION_SERVER.bat`

It will automatically install Flask if needed.

**Option B - Manual installation:**

```bash
pip install flask flask-cors requests
```

**Verify installation:**
```bash
pip show flask
pip show flask-cors
pip show requests
```

---

## Step 4: Test Flask Server

**Using batch file (easiest):**

1. Double-click `RUN_EXTENSION_SERVER.bat`
2. Window should show: `Running on http://localhost:5000/`
3. Leave it running
4. In another window, double-click `TEST_EXTENSION_BACKEND.bat`

**Or manual testing:**

```bash
# Terminal 1: Start Flask server
python flask_server.py

# Terminal 2: Run tests
python test_extension_backend.py
```

**Expected test output:**
```
✅ Server is running!
✅ Connection successful
✅ All tests passed!
```

**If tests fail:** See [WINDOWS_TROUBLESHOOTING.md](WINDOWS_TROUBLESHOOTING.md)

---

## Step 5: Load Extension in Chrome

1. **Open Chrome**
2. **Navigate to extensions page:**
   - Type in address bar: `chrome://extensions/`
   - Or: ⋮ Menu → More Tools → Extensions

3. **Enable Developer Mode:**
   - Toggle in top right corner: "Developer mode"

4. **Load extension:**
   - Click "Load unpacked" button
   - Navigate to: `c:\4TH SEM\Hackathon\phishing-detection\extension\`
   - Click "Select Folder"

5. **Verify extension loaded:**
   - Should see "🔒 Phishing Link Detector" in extensions list
   - Status should be "Enabled" (toggle on if off)
   - Shows a lock icon in Chrome toolbar

---

## Step 6: Test Extension on Websites

**With Flask server running, test the extension:**

1. **Visit a legitimate website:**
   - Go to: https://www.wikipedia.org
   - Click a link
   - Result: Link opens normally (no warning)

2. **Visit a phishing detection test:**
   - Go to: https://phishing.example.com (if available)
   - Click a link that's known phishing
   - Result: Red warning modal appears

3. **Check popup:**
   - Click the lock icon in Chrome toolbar
   - Should show page analysis
   - Green indicator = legitimate page
   - Red indicator = suspicious page

**If extension doesn't work:** See [WINDOWS_TROUBLESHOOTING.md](WINDOWS_TROUBLESHOOTING.md)

---

## Step 7: Verify All Components

**Quick verification checklist:**

```bash
# 1. Python is working
python --version                    # Should show Python x.x.x

# 2. Flask is installed
pip show flask                      # Should show Flask version

# 3. Test script runs
python test_extension_backend.py   # Should show all tests passed

# 4. Extension files exist
dir extension                       # Should list all extension files

# 5. Flask server starts
python flask_server.py             # Should show "Running on..." (press Ctrl+C to stop)
```

---

## Complete File Structure

Your project should now look like this:

```
c:\4TH SEM\Hackathon\phishing-detection\
│
├── 📄 SETUP_VERIFICATION.md              ← YOU ARE HERE
├── 📄 WINDOWS_TROUBLESHOOTING.md         ← Help guide
├── 📄 QUICK_START_EXTENSION.md           ← 5-minute guide
├── 📄 EXTENSION_SETUP.md                 ← Full setup guide
│
├── 🔧 Extension Files (NEW)
│   ├── 📁 extension/
│   │   ├── manifest.json
│   │   ├── background.js
│   │   ├── content.js
│   │   ├── popup.html
│   │   ├── popup.js
│   │   └── icons/
│   │       └── icon-16.svg
│
├── 🍶 Backend (NEW)
│   ├── flask_server.py                   ← Run this to start server
│   ├── RUN_EXTENSION_SERVER.bat          ← Windows: Double-click to start
│   ├── TEST_EXTENSION_BACKEND.bat        ← Windows: Double-click to test
│   ├── test_extension_backend.py         ← Python test script
│
├── 📝 Core Files (EXISTING - unchanged)
│   ├── predict.py
│   ├── feature_extractor.py
│   ├── semantic_detector.py
│   ├── app.py
│   ├── requirements.txt                  ← UPDATED with Flask
│
├── 📁 Data & Models
│   ├── data/phishing.csv
│   ├── model/model.pkl
│   └── notebooks/training.ipynb
│
└── __pycache__/                          ← Auto-generated
```

---

## Quick Start Summary

### For Windows Users (Easiest):

1. **Install Flask (optional - batch file does this):**
   ```bash
   pip install flask flask-cors requests
   ```

2. **Start Flask Server:**
   - Double-click: `RUN_EXTENSION_SERVER.bat`
   - Should stay open

3. **Test in new Command Prompt:**
   - Double-click: `TEST_EXTENSION_BACKEND.bat`
   - Should show "All tests passed! ✅"

4. **Load Extension in Chrome:**
   - Open: `chrome://extensions`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select `extension/` folder

5. **Test on websites:**
   - Click links on webpages
   - Watch for warning modals

### For Advanced Users:

```bash
# Terminal 1: Start server
python flask_server.py

# Terminal 2: Run tests
python test_extension_backend.py

# Then manually load extension:
# - chrome://extensions
# - Load unpacked → select extension folder
```

---

## Common Issues During Setup

| Issue | Solution |
|-------|----------|
| Python not found | Install from python.org, check "Add to PATH" |
| Flask not installed | Run: `pip install flask flask-cors` |
| Port 5000 in use | Kill old process or change port in flask_server.py |
| Extension won't load | Check `extension/manifest.json` exists, reload chrome://extensions |
| Links don't get analyzed | Ensure Flask server is running: `python flask_server.py` |
| Tests fail | See [WINDOWS_TROUBLESHOOTING.md](WINDOWS_TROUBLESHOOTING.md) |

---

## Next Steps

Once setup is verified:

1. **Leave Flask server running** in background
2. **Browse normally** - extension monitors all links
3. **Click any link** - watch for warning modals
4. **Check popup** - click lock icon for full page analysis
5. **Fine-tune** - adjust sensitivity in `extension/content.js` if needed

---

## Support Resources

- **Quick Start:** [QUICK_START_EXTENSION.md](QUICK_START_EXTENSION.md)
- **Setup Guide:** [EXTENSION_SETUP.md](EXTENSION_SETUP.md)
- **Troubleshooting:** [WINDOWS_TROUBLESHOOTING.md](WINDOWS_TROUBLESHOOTING.md)
- **API Reference:** See [EXTENSION_SETUP.md](EXTENSION_SETUP.md#api-endpoints)

---

## Verification Checklist (Final)

After completing all steps, verify:

- [ ] File structure matches above diagram
- [ ] Python version 3.8+: `python --version`
- [ ] Flask installed: `pip show flask`
- [ ] All extension files exist: `dir extension`
- [ ] Flask server starts: `python flask_server.py` (shows "Running on...")
- [ ] Tests pass: `python test_extension_backend.py` (shows "All tests passed")
- [ ] Extension loads: `chrome://extensions` shows "🔒 Phishing Link Detector"
- [ ] Extension works: Click a link on any webpage

✅ **If all checks pass, you're ready to use the extension!**

---

**Last Updated:** January 2024  
**Tested On:** Windows 10, Windows 11  
**Python:** 3.8+ required  
**Chrome:** 120+ recommended
