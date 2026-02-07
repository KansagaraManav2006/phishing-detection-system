"""
Test utility for Phishing Detection Extension Backend

Run this script to verify the Flask server is working correctly
before using the browser extension.

USAGE:
    python test_extension_backend.py
"""

import requests
import json
import sys
from pathlib import Path

# Configuration
BACKEND_URL = 'http://localhost:5000'
API_ENDPOINT = f'{BACKEND_URL}/predict'

# Test cases
TEST_URLS = [
    {
        'url': 'https://www.wikipedia.org',
        'expected': 'Safe',
        'description': 'Legitimate Wikipedia'
    },
    {
        'url': 'http://google.com.verify-user.ru/login',
        'expected': 'Phishing',
        'description': 'Obvious phishing (brand spoofing)'
    },
    {
        'url': 'https://github.com',
        'expected': 'Safe',
        'description': 'Legitimate GitHub'
    },
    {
        'url': 'http://paypal-verify.tk',
        'expected': 'Phishing',
        'description': 'Spoofed PayPal with suspicious TLD'
    },
]

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")

def test_server_connection():
    """Test if Flask server is running"""
    print_header("Testing Server Connection")
    
    try:
        response = requests.get(f'{BACKEND_URL}/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server is running! ({data.get('service', 'Unknown')})")
            print(f"   Version: {data.get('version', 'Unknown')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
            return True
        else:
            print_error(f"Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot reach Flask server at http://localhost:5000")
        print("\n   Make sure to run: python flask_server.py")
        return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

def test_prediction_api():
    """Test the prediction API"""
    print_header("Testing Prediction API")
    
    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    for test in TEST_URLS:
        url = test['url']
        expected = test['expected']
        description = test['description']
        
        try:
            print(f"\nTesting: {description}")
            print(f"URL: {url}")
            
            response = requests.post(
                API_ENDPOINT,
                json={'url': url},
                timeout=10
            )
            
            if response.status_code != 200:
                print_error(f"API returned status {response.status_code}")
                results['failed'] += 1
                results['errors'].append({
                    'url': url,
                    'error': f"HTTP {response.status_code}"
                })
                continue
            
            data = response.json()
            
            if not data.get('success', False):
                print_error(f"API error: {data.get('error', 'Unknown error')}")
                results['failed'] += 1
                results['errors'].append({
                    'url': url,
                    'error': data.get('error', 'Unknown')
                })
                continue
            
            # Extract prediction values
            label = data.get('label')
            probability = data.get('probability', 0)
            risk_category = data.get('risk_category', 'Unknown')
            
            # Determine if Safe or Phishing
            prediction = 'Phishing' if label == 1 else 'Safe'
            
            # Check if matches expectation
            is_correct = (expected == 'Phishing' and label == 1) or \
                        (expected == 'Safe' and label == 0)
            
            print(f"Prediction: {prediction} ({probability*100:.1f}%)")
            print(f"Risk Level: {risk_category}")
            
            if is_correct:
                print_success(f"Correct! (Expected: {expected})")
                results['passed'] += 1
            else:
                print_error(f"Unexpected! (Expected: {expected})")
                results['failed'] += 1
                
        except requests.exceptions.Timeout:
            print_error("Request timed out (server too slow?)")
            results['failed'] += 1
        except Exception as e:
            print_error(f"Error: {str(e)}")
            results['failed'] += 1
            results['errors'].append({
                'url': url,
                'error': str(e)
            })
    
    return results

def test_batch_api():
    """Test batch prediction API"""
    print_header("Testing Batch Prediction API")
    
    batch_urls = [
        'https://www.google.com',
        'http://fake-google.ru',
        'https://github.com'
    ]
    
    try:
        response = requests.post(
            f'{BACKEND_URL}/batch',
            json={'urls': batch_urls},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            print_success(f"Batch API works! Analyzed {len(results)} URLs")
            
            for result in results:
                url = result.get('url', 'Unknown')
                if 'error' in result:
                    print(f"  ❌ {url}: {result['error']}")
                else:
                    prob = result.get('probability', 0)
                    risk = result.get('risk_category', 'Unknown')
                    pred = 'Phishing' if result.get('label') == 1 else 'Safe'
                    print(f"  ✅ {url}")
                    print(f"     → {pred} ({prob*100:.1f}%) - {risk}")
            
            return True
        else:
            print_error(f"Batch API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Batch API error: {str(e)}")
        return False

def test_features_api():
    """Test feature extraction API"""
    print_header("Testing Feature Extraction API")
    
    test_url = 'http://example.com'
    
    try:
        response = requests.post(
            f'{BACKEND_URL}/features',
            json={'url': test_url},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', {})
            
            print_success(f"Feature extraction works!")
            print(f"Extracted {len(features)} features for: {test_url}")
            
            # Show first 5 features
            print("\nSample features:")
            for i, (key, value) in enumerate(list(features.items())[:5]):
                print(f"  {key}: {value}")
            
            if len(features) > 5:
                print(f"  ... and {len(features) - 5} more")
            
            return True
        else:
            print_error(f"Features API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Features API error: {str(e)}")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")
    
    passed = results.get('passed', 0)
    failed = results.get('failed', 0)
    total = passed + failed
    
    if total == 0:
        print_error("No tests were run")
        return False
    
    percentage = (passed / total) * 100
    
    print(f"Tests Passed: {passed}/{total} ({percentage:.0f}%)")
    
    if failed > 0:
        print(f"Tests Failed: {failed}/{total}")
        
        if results.get('errors'):
            print("\nErrors:")
            for error in results['errors']:
                print(f"  - {error.get('url', 'Unknown')}: {error.get('error', 'Unknown')}")
    
    print()
    
    if percentage == 100:
        print_success("All tests passed! ✅")
        print("\nYour extension backend is ready to use.")
        print("Now you can:")
        print("  1. Load the extension in Chrome (chrome://extensions/)")
        print("  2. Browse to any website")
        print("  3. Click links - the extension will check them")
        return True
    else:
        print_error(f"Some tests failed (only {percentage:.0f}% passed)")
        print("\nCheck the Flask server is running:")
        print("  python flask_server.py")
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*15 + "🔒 Extension Backend Tests" + " "*17 + "║")
    print("╚" + "═"*58 + "╝")
    
    results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # Test 1: Server connection
    if not test_server_connection():
        print_error("\nCannot connect to Flask server")
        print("\nStart the server with:")
        print("  python flask_server.py")
        return 1
    
    # Test 2: Prediction API
    pred_results = test_prediction_api()
    results['passed'] += pred_results['passed']
    results['failed'] += pred_results['failed']
    results['errors'] += pred_results['errors']
    
    # Test 3: Batch API
    test_batch_api()
    
    # Test 4: Features API
    test_features_api()
    
    # Print summary
    success = print_summary(results)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
