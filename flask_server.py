r"""Flask Backend Server for Phishing Detection Extension

WHY THIS FILE?
==============
The browser extension needs to analyze URLs quickly from web pages.
The ML model and 41 feature extraction are compute-intensive,
so we run them on a backend Flask server instead of in the extension.

ARCHITECTURE:
┌─────────────────────────────────────────────┐
│ User's Browser                              │
│ ├─ Web Page with Links                      │
│ ├─ Extension Content Script                 │
│ │  └─ Detects link click                    │
│ │  └─ Sends URL to Flask server (API call)  │
│ │  └─ Displays warning if phishing          │
│ └─ Extension Background Script              │
│    └─ Caches results, manages communication │
│                                             │
└─────────────────────────────────────────────┘
              ↕ HTTP API Call
┌─────────────────────────────────────────────┐
│ Flask Server (localhost:5000)               │
│ ├─ Load RandomForest model                  │
│ ├─ Extract 41 features                      │
│ ├─ Get ML probability                       │
│ ├─ Execute semantic rules                   │
│ ├─ Combine hybrid prediction                │
│ └─ Return JSON response                     │
└─────────────────────────────────────────────┘

HOW TO RUN:
===========
1. cd c:\4TH SEM\Hackathon\phishing-detection
2. python flask_server.py
3. Server runs on http://localhost:5000
4. Chrome extension calls /predict endpoint
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import logging
import sys
import json
from datetime import datetime

# Add parent directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

from predict import predict_url
from feature_extractor import extract_features_from_url

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests from extension

# Configuration
app.config['JSON_SORT_KEYS'] = False

# Force logs to stdout so VS terminal always shows them
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter('%(message)s'))
app.logger.handlers = [_handler]
app.logger.setLevel(logging.INFO)
app.logger.propagate = False


def log_api(message):
    timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
    app.logger.info(f"[API] {message}")
    return timestamp


@app.after_request
def log_request(response):
    timestamp = datetime.now().strftime('%d/%b/%Y %H:%M:%S')
    method = request.method
    path = request.path
    proto = request.environ.get('SERVER_PROTOCOL', 'HTTP/1.1')
    client = request.remote_addr or '127.0.0.1'
    status = response.status_code
    app.logger.info(f"{client} - - [{timestamp}] \"{method} {path} {proto}\" {status}")
    return response


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint - extension can use to verify server is running
    
    RESPONSE: {"status": "ok", "version": "1.0.0"}
    """
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "service": "Phishing Detection Backend"
    }), 200


@app.route('/predict', methods=['POST', 'OPTIONS'])
def predict():
    """
    Main prediction endpoint - called by extension content script
    
    REQUEST:
    --------
    POST /predict
    {
        "url": "http://google.com.verify-user.ru/login"
    }
    
    RESPONSE:
    ---------
    {
        "label": 1,                              // 0=legitimate, 1=phishing
        "probability": 1.0,                      // 0-1 confidence score
        "risk_category": "High Risk Phishing",   // User-friendly category
        "success": true
    }
    
    ERROR RESPONSE:
    ---------------
    {
        "error": "Invalid URL",
        "success": false
    }
    """
    
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Get URL from request
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                "error": "Missing 'url' parameter",
                "success": False
            }), 400
        
        url = data['url'].strip()
        
        if not url:
            return jsonify({
                "error": "URL cannot be empty",
                "success": False
            }), 400
        
        # Validate URL format (basic check)
        if not (url.startswith('http://') or url.startswith('https://')):
            # Add scheme if missing
            url = 'http://' + url
        
        log_api(f"Analyzing: {url}")
        
        # Get prediction from our ML system
        label, probability, risk_category = predict_url(url)
        
        # Return response
        response = {
            "label": label,
            "probability": float(probability),
            "risk_category": risk_category,
            "success": True
        }
        
        log_api(f"Result: {risk_category} ({probability*100:.1f}%)")
        
        return jsonify(response), 200
        
    except Exception as e:
        app.logger.error(f"[Error] Prediction failed: {str(e)}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.route('/features', methods=['POST'])
def get_features():
    """
    Additional endpoint to get feature details for a URL
    
    Useful for debugging and understanding why a URL was flagged
    
    REQUEST:
    --------
    POST /features
    {
        "url": "http://example.com"
    }
    
    RESPONSE:
    ---------
    {
        "url": "http://example.com",
        "features": {
            "url_length": 18,
            "number_of_dots_in_url": 1,
            ... (all 41 features)
        }
    }
    """
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "URL required"}), 400
        
        features = extract_features_from_url(url)
        
        return jsonify({
            "url": url,
            "features": features.iloc[0].to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/batch', methods=['POST'])
def batch_predict():
    """
    Batch prediction endpoint - analyze multiple URLs at once
    
    REQUEST:
    --------
    POST /batch
    {
        "urls": [
            "http://example1.com",
            "http://example2.com"
        ]
    }
    
    RESPONSE:
    ---------
    {
        "results": [
            {
                "url": "http://example1.com",
                "label": 0,
                "probability": 0.15,
                "risk_category": "Safe"
            },
            ...
        ],
        "success": true
    }
    """
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not isinstance(urls, list) or len(urls) == 0:
            return jsonify({"error": "urls must be a non-empty array"}), 400
        
        results = []
        for url in urls:
            try:
                log_api(f"Batch analyzing: {url}")
                label, probability, risk_category = predict_url(url)
                log_api(f"Batch result: {risk_category} ({probability*100:.1f}%)")
                results.append({
                    "url": url,
                    "label": label,
                    "probability": float(probability),
                    "risk_category": risk_category
                })
            except Exception as e:
                app.logger.error(f"[Error] Batch prediction failed: {str(e)}")
                results.append({
                    "url": url,
                    "error": str(e)
                })
        
        return jsonify({
            "results": results,
            "success": True
        }), 200
        
    except Exception as e:
        app.logger.error(f"[Error] Batch request failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "POST /predict - Single URL prediction",
            "POST /batch - Batch URL predictions",
            "POST /features - Extract features for URL",
            "GET /health - Server health check"
        ]
    }), 404


@app.errorhandler(500)
def server_error(error):
    """Handle server errors"""
    app.logger.error(f"[Server Error] {error}")
    return jsonify({
        "error": "Internal server error",
        "message": str(error)
    }), 500


if __name__ == '__main__':
    print(r"""
    ╔═══════════════════════════════════════════════════════════╗
    ║  🔒 Phishing Detection Backend Server                    ║
    ║                                                           ║
    ║  Server: http://localhost:5000                           ║
    ║  API Endpoints:                                          ║
    ║    POST /predict  - Analyze single URL                   ║
    ║    POST /batch    - Analyze multiple URLs                ║
    ║    POST /features - Get feature breakdown                ║
    ║    GET  /health   - Server health check                  ║
    ║                                                           ║
    ║  Chrome extension connects here for URL analysis         ║
    ║                                                           ║
    ║  To test: python -m curl -X POST http://localhost:5000/predict \\
    ║           -H "Content-Type: application/json" \\
    ║           -d '{"url":"https://example.com"}'             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Run server
    # debug=True enables auto-reload on code changes
    # threaded=True allows multiple requests simultaneously
    app.run(
        host='localhost',
        port=5000,
        debug=True,
        threaded=True,
        use_reloader=False  # Disable auto-reload in production
    )
