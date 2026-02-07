# 🛡️ Phishing Detection System

A comprehensive phishing detection system that combines machine learning and browser extension technology to protect users from phishing attacks in real-time.

## 📋 Overview

This project provides a multi-layered approach to phishing detection:
- **Machine Learning Model**: Trained classifier to detect phishing URLs based on various features
- **Semantic Analysis**: Natural language processing to identify suspicious content
- **Browser Extension**: Real-time protection while browsing
- **Flask Backend**: RESTful API for URL analysis

## ✨ Features

- ✅ Real-time URL scanning and analysis
- ✅ Machine learning-based phishing detection
- ✅ Semantic content analysis
- ✅ Browser extension for Chrome/Edge
- ✅ Visual warning system for suspicious links
- ✅ Automatic link interception and protection
- ✅ Easy-to-use API for integration

## 🏗️ Project Structure

```
phishing-detection/
├── app.py                          # Main application entry point
├── flask_server.py                 # Flask API server
├── feature_extractor.py            # URL feature extraction module
├── predict.py                      # Prediction logic
├── semantic_detector.py            # Semantic analysis module
├── requirements.txt                # Python dependencies
├── data/
│   └── phishing.csv               # Training dataset
├── model/
│   ├── model.pkl                  # Trained ML model
│   └── vectorizer.pkl             # Text vectorizer
├── extension/
│   ├── manifest.json              # Extension configuration
│   ├── background.js              # Background service worker
│   ├── content.js                 # Content script
│   ├── popup.html/js              # Extension popup UI
│   ├── warning.html/js            # Warning page
│   └── icons/                     # Extension icons
└── notebooks/
    └── training.ipynb             # Model training notebook
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Chrome or Edge browser
- pip (Python package installer)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/KansagaraManav2006/phishing-detection-system.git
   cd phishing-detection-system
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask server**
   ```bash
   python flask_server.py
   ```
   
   Or use the provided batch file (Windows):
   ```bash
   RUN_EXTENSION_SERVER.bat
   ```

   The server will start at `http://localhost:5000`

### Browser Extension Setup

1. **Open Chrome/Edge**
   - Navigate to `chrome://extensions/` or `edge://extensions/`

2. **Enable Developer Mode**
   - Toggle the "Developer mode" switch in the top right

3. **Load the Extension**
   - Click "Load unpacked"
   - Select the `extension` folder from this project

4. **Start Browsing Safely**
   - The extension will automatically protect you from phishing sites

## 📊 API Endpoints

### Check URL
```http
POST /check_url
Content-Type: application/json

{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "is_phishing": false,
  "confidence": 0.95,
  "features": {...}
}
```

## 🔧 Configuration

### Server Configuration
- Default port: `5000`
- Modify in `flask_server.py` if needed

### Extension Configuration
- API endpoint configured in `extension/background.js`
- Change `API_URL` constant to match your server

## 🧪 Testing

Test the backend API:
```bash
python test_extension_backend.py
```

Or use the provided batch file (Windows):
```bash
TEST_EXTENSION_BACKEND.bat
```

## 📚 Documentation

Additional documentation available:
- [Extension Setup Guide](EXTENSION_SETUP.md)
- [Quick Start Guide](QUICK_START_EXTENSION.md)
- [Code Explanations](CODE_EXPLANATIONS.md)
- [System Summary](SYSTEM_SUMMARY.md)
- [Windows Troubleshooting](WINDOWS_TROUBLESHOOTING.md)

## 🤖 Machine Learning Model

The system uses a trained machine learning model that analyzes:
- URL structure and patterns
- Domain characteristics
- SSL certificate information
- Content features
- Semantic indicators

The model is trained on a comprehensive dataset of phishing and legitimate URLs.

## 🛠️ Development

### Training the Model

Open and run the Jupyter notebook:
```bash
jupyter notebook notebooks/training.ipynb
```

### Extending the System

- Add new features in `feature_extractor.py`
- Modify detection logic in `predict.py`
- Enhance semantic analysis in `semantic_detector.py`

## 🔒 Security Features

- Real-time URL scanning
- Pre-navigation warnings
- Visual indicators for suspicious links
- Automatic blocking of confirmed phishing sites
- Semantic content analysis

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available for educational purposes.

## 👨‍💻 Author

**Manav Kansagara**
- GitHub: [@KansagaraManav2006](https://github.com/KansagaraManav2006)

## ⚠️ Disclaimer

This tool is designed to assist in detecting phishing attempts but should not be solely relied upon. Always exercise caution when clicking on links and providing sensitive information online.

## 🙏 Acknowledgments

- Built as part of a hackathon project
- Uses machine learning for phishing detection
- Inspired by the need for better online security

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Stay Safe Online! 🛡️**
