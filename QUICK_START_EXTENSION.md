# 🚀 QUICK START - Browser Extension Setup

Get your phishing detection extension running in **5 minutes**!

## Step 1: Install Dependencies (1 minute)

```bash
cd c:\4TH SEM\Hackathon\phishing-detection
pip install flask flask-cors
```

## Step 2: Start Backend Server (30 seconds)

Open a **new PowerShell terminal** and run:

```bash
cd c:\4TH SEM\Hackathon\phishing-detection
python flask_server.py
```

Wait for this message:
```
Running on http://localhost:5000
```

**Keep this terminal open!** Don't close it.

## Step 3: Load Extension in Chrome (1 minute)

### Option A: Manual Loading (Recommended for Development)

1. **Open Chrome**
2. Go to: `chrome://extensions/`
3. **Turn on "Developer mode"** (toggle in top-right)
4. Click **"Load unpacked"**
5. Navigate to: `c:\4TH SEM\Hackathon\phishing-detection\extension\`
6. Click **Select Folder**
7. You should see: `🔒 Phishing Link Detector` appear in your extensions

### Option B: Quick Terminal Load

```bash
# Windows PowerShell
start "chrome://extensions/"
```

Then follow steps 3-7 above.

## Step 4: Test It! (2 minutes)

### Test on Real Sites

1. **Open any website** (e.g., Wikipedia)
2. **Click on a link** - Extension analyzes it
3. **Should work silently** for legitimate links
4. **Try this test URL** - Opens a special test warning:
   ```
   Open new tab → paste this URL:
   http://google.com.verify-user.ru/login
   
   Click any link on the page → Should show warning!
   ```

### Expected Behavior

- 🟢 **Legitimate links**: Open normally (quiet)
- 🟠 **Suspicious links**: Show warning modal
- 🔴 **Phishing links**: Red warning + block

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| **"Cannot reach server"** | Flask server not running. Run `python flask_server.py` in new terminal |
| **Extension not loading** | Check path: `extension/manifest.json` should exist |
| **Links not blocked** | Refresh the page (F5), try clicking link again |
| **Slow performance** | Check Flask terminal for error messages |

---

## Architecture Overview

```
When you click a link on any website:

1. Your click is detected by content.js running on the page
2. Extension sends URL to Flask backend: POST http://localhost:5000/predict
3. Backend analyzes URL:
   - Extracts 41 features
   - Queries RandomForest model
   - Runs semantic rules
   - Returns {label, probability, risk_category}
4. Extension shows warning if confidence >= 60%
5. You decide: Open or Cancel
```

## File Structure

```
YOUR PROJECT FOLDER:
├── extension/               ← Browser extension
│   ├── manifest.json       (Configuration)
│   ├── background.js       (API communication)
│   ├── content.js          (Link monitoring + warnings)
│   ├── popup.html          (Popup UI)
│   ├── popup.js            (Popup logic)
│   └── icons/              (Extension icons)
│
├── flask_server.py         ← Backend API
├── predict.py              ← ML prediction
├── feature_extractor.py    ← Feature extraction
├── semantic_detector.py     ← Rule-based detection
└── model/model.pkl         ← Trained model
```

## Testing Console Logs

See what's happening behind the scenes:

1. On any webpage, press **F12** (DevTools)
2. Go to **Console** tab
3. You'll see messages like:
   ```
   [Phishing Detector] Content script loaded
   [Content] Prediction for https://example.com: ...
   [Warning] Detected potential phishing: ...
   ```

## Common Test URLs

### Should Trigger Warnings 🚨
```
http://google.com.verify-user.ru/login
http://paypal-confirm.tk/account
http://amazon-verify.click/login
http://apple-id-verify.ml/signin
```

### Should Pass Safely ✅
```
https://www.wikipedia.org
https://github.com
https://stackoverflow.com
https://www.google.com
```

## Next Steps

### To Customize
- Edit `extension/content.js` to change sensitivity
- Edit `extension/background.js` to change server URL
- Change colors in `content.js` CSS section

### To Deploy
- See `EXTENSION_SETUP.md` for production guide
- Publish to Chrome Web Store for users

### To Extend
- Add Firefox support (different manifest)
- Add whitelisting feature
- Add phishing stats dashboard
- Integrate with incident reporting

---

**Enjoy your phishing-protected browsing! 🔒**

Need help? Check the full setup guide: [`EXTENSION_SETUP.md`](./EXTENSION_SETUP.md)
