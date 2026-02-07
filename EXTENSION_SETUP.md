# 🔒 Phishing Detection Browser Extension

Convert your phishing detection system into a Chrome browser extension that protects users in real-time!

## What It Does

- ✅ **Monitors all links** on every webpage you visit
- ✅ **Analyzes URLs** before you click them using our ML model
- ✅ **Shows warning** if a link is potentially phishing
- ✅ **Lets you decide** - block or open anyway
- ✅ **Fast & intelligent** - runs hybrid ML + semantic detection

## Architecture

```
┌────────────────────────────────────────────────────┐
│ Chrome Browser                                     │
│ ├─ Web Page with Links                            │
│ ├─ popup.js (Extension icon popup)               │
│ ├─ content.js (Monitors links, shows warnings)    │
│ └─ background.js (Manages API communication)      │
│         │                                          │
│         │ HTTP POST                                │
│         ↓                                          │
│ Flask Server (localhost:5000)                     │
│ ├─ Loads RandomForest model                       │
│ ├─ Extracts 41 features                           │
│ ├─ Hybrid ML + Semantic prediction                │
│ └─ Returns JSON response                          │
└────────────────────────────────────────────────────┘
```

## Installation & Setup

### Step 1: Install Dependencies

```bash
cd c:\4TH SEM\Hackathon\phishing-detection
pip install flask flask-cors
```

### Step 2: Start Flask Backend Server

In a **new terminal**:

```bash
cd c:\4TH SEM\Hackathon\phishing-detection
python flask_server.py
```

You should see:
```
╔═══════════════════════════════════════════════════════════╗
║  🔒 Phishing Detection Backend Server                    ║
║  Server: http://localhost:5000                           ║
╚═══════════════════════════════════════════════════════════╝
```

**Keep this terminal open!** The server must be running for the extension to work.

### Step 3: Load Extension in Chrome

1. **Open Chrome** and go to: `chrome://extensions/`

2. **Enable Developer Mode**
   - Toggle in top-right corner

3. **Click "Load unpacked"**
   - Navigate to: `c:\4TH SEM\Hackathon\phishing-detection\extension\`
   - Click Select Folder

4. **Extension Appears**
   - You should see "🔒 Phishing Link Detector" in your extensions
   - Pin it to your toolbar for easy access

## How to Use

### Basic Usage

1. **Browse normally** - Extension is always monitoring

2. **Hover over or click a link** - Extension analyzes it instantly

3. **See warning if phishing detected**:
   ```
   ⚠️ Potential Phishing Link Detected
   
   Risk Level: High Risk Phishing
   Phishing Confidence: 95.4%
   
   [🛑 Don't Open Link] [⚠️ Open Anyway]
   ```

4. **Choose action**:
   - `Don't Open Link` - Blocks the navigation (safe!)
   - `Open Anyway` - Proceeds at your own risk
   - Press `Escape` - Closes warning

### Check Current Page

1. **Click extension icon** in toolbar
2. **Popup shows**:
   - Current page status (Safe/Suspicious/High Risk)
   - Confidence percentage
   - Current URL

## File Structure

```
extension/
├── manifest.json          # Extension configuration
├── background.js          # Service worker (manages API calls)
├── content.js            # Page script (monitors links, shows UI)
├── popup.html            # Popup UI
├── popup.js              # Popup logic
└── icons/                # Extension icons
    ├── icon-16.png
    ├── icon-48.png
    └── icon-128.png

Parent folder:
├── flask_server.py       # Backend API server
├── predict.py            # ML prediction engine
├── feature_extractor.py  # Feature extraction
├── semantic_detector.py   # Semantic rules
└── model/model.pkl       # Trained RandomForest model
```

## Configuration

### Backend URL

To change the backend server address, edit `extension/background.js`:

```javascript
const BACKEND_URL = 'http://localhost:5000/predict';  // Change this
```

For production, use your deployed server:
```javascript
const BACKEND_URL = 'https://your-server.com/predict';
```

### Sensitivity Threshold

Edit `extension/content.js` to change when warnings appear:

```javascript
// Show warning if phishing confidence >= 60%
if (prediction.probability >= 0.6) {  // Change this
    showPhishingWarning(url, prediction);
}
```

- `0.5` = Show warnings for 50%+ confidence (very sensitive)
- `0.6` = Default (balanced)
- `0.8` = Only high-confidence warnings (less sensitive)

## API Endpoints

The Flask server provides these endpoints:

### POST /predict
Analyze a single URL

**Request:**
```json
{
    "url": "http://google.com.verify-user.ru/login"
}
```

**Response:**
```json
{
    "label": 1,
    "probability": 1.0,
    "risk_category": "High Risk Phishing",
    "success": true
}
```

### POST /batch
Analyze multiple URLs at once

**Request:**
```json
{
    "urls": [
        "http://example1.com",
        "http://example2.com"
    ]
}
```

### POST /features
Get detailed feature breakdown for a URL

**Request:**
```json
{
    "url": "http://example.com"
}
```

**Response:**
```json
{
    "url": "http://example.com",
    "features": {
        "url_length": 18,
        "number_of_dots_in_url": 1,
        ...
    }
}
```

### GET /health
Check if server is running

**Response:**
```json
{
    "status": "ok",
    "version": "1.0.0",
    "service": "Phishing Detection Backend"
}
```

## Troubleshooting

### Extension Won't Work

1. **Check Flask server is running**
   ```bash
   # Should see "Running on http://localhost:5000"
   ```

2. **Check console for errors**
   - Press F12 in Chrome
   - Go to Console tab
   - Look for error messages

3. **Reload extension**
   - Go to `chrome://extensions/`
   - Click reload button (circular arrow)

### "Backend Unavailable" Error

This means the Flask server isn't running:

```bash
# In new terminal:
cd c:\4TH SEM\Hackathon\phishing-detection
python flask_server.py
```

### Links Not Being Intercepted

1. **Check content.js is running**
   - Open DevTools (F12)
   - Go to Console
   - Should show: `[Phishing Detector] Content script loaded`

2. **Some sites block extensions**
   - Extensions can't run on: `chrome://*`, `https://chrome.google.com`, etc.
   - This is a security feature

3. **Reload the page**
   - F5 or Ctrl+R
   - Then try clicking links

## Testing

### Test Phishing URLs

Try these test URLs to see the warning:

```
http://google.com.verify-user.ru/login
http://amazon-verify.click/account
http://paypa1.com/confirm
http://login.banking-confirm.tk/secure
```

### Test Legitimate URLs

These should show green/safe:

```
https://www.wikipedia.org
https://github.com
https://www.google.com
https://stackoverflow.com
```

### Quick API Test

```bash
# Test Flask server directly
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"http://evil.tk\"}"
```

## Performance Notes

- **First load**: ~1-2 seconds (backend response + modal creation)
- **Subsequent loads**: <100ms (cached results)
- **Memory**: Caches URLs for 1 hour to reduce API calls
- **CPU**: Minimal impact - only analyzes when hovering/clicking links

## Security Considerations

1. **Backend Security**: Keep Flask server on localhost in production
2. **CORS**: Set up proper CORS headers for your domain
3. **SSL**: Use HTTPS in production (`https://your-domain.com/predict`)
4. **Rate Limiting**: Consider adding rate limiting to backend
5. **API Key**: Add authentication token for production deployment

## For Production Deployment

### 1. Deploy Flask Server

Use a production server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 flask_server:app
```

### 2. Update Extension

Change backend URL in `extension/background.js`:

```javascript
const BACKEND_URL = 'https://your-domain.com/api/predict';
```

### 3. Publish to Chrome Web Store

1. Go to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole)
2. Create developer account
3. Upload extension bundle (`.zip` of extension folder)
4. Add screenshots and description
5. Submit for review

## Future Enhancements

- [ ] **Firefox version** - Different manifest for Firefox
- [ ] **Edge support** - Microsoft Edge compatibility
- [ ] **Offline mode** - ONNX model in extension for offline detection
- [ ] **Detailed reports** - Save analysis history
- [ ] **Whitelisting** - Let users whitelist safe domains
- [ ] **Dashboard** - Statistics and blocked phishing attempts
- [ ] **Real-time updates** - Automatic extension updates
- [ ] **Machine learning** - Learn from user feedback

## Support

### Common Issues

**Q: Extension shows "offline" message**
A: Start Flask server: `python flask_server.py`

**Q: Links open without warning**
A: Lower sensitivity threshold in `content.js`

**Q: Extension is slow**
A: Flask server may be overloaded - check terminal output

### Debug Mode

Enable detailed logging:

1. Edit `extension/background.js`
2. Uncomment `console.log()` statements
3. Open DevTools (F12) in extension popup
4. Go to Console tab - see all API calls

## License

This extension uses your phishing detection system. Keep credentials secure!

---

**Happy browsing! 🔒 Stay safe from phishing!**
