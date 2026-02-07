/**
 * Background Service Worker for Phishing Detection Extension
 * 
 * AUTOMATIC URL INTERCEPTION - METHOD 1: webRequest API
 * ======================================================
 * This script intercepts ALL navigation requests BEFORE they load.
 * Flow: WhatsApp link → Browser → Extension intercepts → Check → Block/Allow
 * 
 * Features:
 * 1. Intercepts URLs using chrome.webRequest.onBeforeRequest
 * 2. Checks against ML backend (Flask server)
 * 3. Redirects to warning page if phishing detected
 * 4. Comprehensive terminal logging
 * 5. Caching to avoid redundant checks
 */

// Configuration
const BACKEND_URL = 'http://localhost:5000/predict';
const CACHE_DURATION = 3600000; // 1 hour
const PHISHING_BLOCK_THRESHOLD = 0.80; // 80% confidence = BLOCK
const PHISHING_WARN_THRESHOLD = 0.60;  // 60% confidence = WARN
const urlCache = new Map();
const pendingChecks = new Map(); // Prevent duplicate concurrent checks

// Whitelist of trusted domains (skip phishing check for these)
const TRUSTED_DOMAINS = new Set([
  'google.com', 'youtube.com', 'gmail.com', 'google.co.in', 'google.co.uk',
  'facebook.com', 'instagram.com', 'whatsapp.com',
  'microsoft.com', 'live.com', 'outlook.com', 'office.com', 'bing.com',
  'apple.com', 'icloud.com',
  'amazon.com', 'amazon.in', 'amazon.co.uk',
  'twitter.com', 'x.com',
  'linkedin.com',
  'github.com', 'stackoverflow.com',
  'wikipedia.org', 'reddit.com',
  'yahoo.com', 'netflix.com',
  'paypal.com',
  'ebay.com',
  'adobe.com'
]);

const HEURISTIC_TLDS = new Set([
  'tk', 'ru', 'cn', 'info', 'shop', 'site', 'online', 'link', 'top', 'xyz', 'buzz', 'click',
  'help', 'support'
]);

const BRAND_KEYWORDS = [
  'paypal', 'google', 'facebook', 'apple', 'appleid', 'amazon', 'netflix',
  'microsoft', 'instagram', 'bankofamerica', 'boa'
];

const AUTH_KEYWORDS = [
  'login', 'signin', 'verify', 'verification', 'secure', 'security', 'support',
  'account', 'update', 'confirm', 'reset', 'payment', 'billing', 'alert',
  'notify', 'notice', 'offer', 'deals', 'deal', 'banking', 'share', 'docs', 'doc'
];

function getHeuristicRisk(url) {
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase();
    const path = parsed.pathname.toLowerCase();
    const combined = `${host}${path}`;
    const parts = host.split('.');
    const tld = parts[parts.length - 1] || '';

    let score = 0;
    const reasons = [];

    if (parsed.protocol === 'http:') {
      score += 1;
      reasons.push('http');
    }

    if (host.includes('xn--')) {
      score += 2;
      reasons.push('punycode');
    }

    const hyphenCount = (host.match(/-/g) || []).length;
    if (hyphenCount >= 2) {
      score += 1;
      reasons.push('many-hyphens');
    }

    const dotCount = (host.match(/\./g) || []).length;
    if (dotCount >= 3) {
      score += 1;
      reasons.push('many-subdomains');
    }

    if (HEURISTIC_TLDS.has(tld)) {
      score += 1;
      reasons.push('risky-tld');
    }

    const hasBrand = BRAND_KEYWORDS.some((b) => combined.includes(b));
    const hasAuth = AUTH_KEYWORDS.some((k) => combined.includes(k));
    if (hasBrand && hasAuth) {
      score += 2;
      reasons.push('brand-plus-auth');
    } else if (hasAuth) {
      score += 1;
      reasons.push('auth-keyword');
    }

    let level = 'allow';
    if (score >= 4) level = 'block';
    else if (score >= 2) level = 'warn';

    return { level, score, reasons };
  } catch (error) {
    return { level: 'allow', score: 0, reasons: [] };
  }
}

// Logging helper
function log(type, message, data = null) {
  const timestamp = new Date().toLocaleTimeString();
  const prefix = `[${timestamp}] [${type}]`;
  
  if (data) {
    console.log(`${prefix} ${message}`, data);
  } else {
    console.log(`${prefix} ${message}`);
  }
}

/**
 * Fetch prediction from Flask backend server
 * @param {string} url - URL to analyze
 * @returns {Promise<Object>} - {label, probability, risk_category}
 */
async function getPrediction(url) {
  try {
    const cacheKey = url.toLowerCase();
    const cached = urlCache.get(cacheKey);
    
    // Return cached result if still fresh
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      log('CACHE', `\u2705 Cache hit for: ${url}`);
      return cached.data;
    }
    
    // Check if already being processed
    if (pendingChecks.has(cacheKey)) {
      log('WAIT', `\u23f3 Already checking: ${url}`);
      return await pendingChecks.get(cacheKey);
    }
    
    // Make API call to backend
    log('API', `\ud83d\udd0d Analyzing URL: ${url}`);
    
    const promise = fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url }),
      signal: AbortSignal.timeout(5000) // 5 second timeout
    })
    .then(async response => {
      if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
      }
      const result = await response.json();
      
      // Log the result with details
      const confidence = (result.probability * 100).toFixed(1);
      const icon = result.probability >= PHISHING_BLOCK_THRESHOLD ? '❌' : 
                   result.probability >= PHISHING_WARN_THRESHOLD ? '⚠️' : '✅';
      
      log('RESULT', `${icon} ${url}`, {
        confidence: `${confidence}%`,
        category: result.risk_category,
        label: result.label === 1 ? 'PHISHING' : 'SAFE'
      });
      
      // Cache the result
      urlCache.set(cacheKey, {
        data: result,
        timestamp: Date.now()
      });
      
      pendingChecks.delete(cacheKey);
      return result;
    });
    
    pendingChecks.set(cacheKey, promise);
    return await promise;
    
  } catch (error) {
    log('ERROR', `⚠️ Failed to analyze: ${url}`, error.message);
    pendingChecks.delete(url.toLowerCase());
    
    return {
      label: 0,
      probability: 0,
      risk_category: "Unknown",
      error: error.message
    };
  }
}

/**
 * Check if a URL belongs to a trusted domain
 * @param {string} url - URL to check
 * @returns {boolean} - true if domain is trusted
 */
function isTrustedDomain(url) {
  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.toLowerCase();
    
    // Check exact match
    if (TRUSTED_DOMAINS.has(hostname)) return true;
    
    // Check if it's a subdomain of a trusted domain
    for (const trustedDomain of TRUSTED_DOMAINS) {
      if (hostname === trustedDomain || hostname.endsWith('.' + trustedDomain)) {
        return true;
      }
    }
    
    return false;
  } catch (error) {
    return false;
  }
}

/**
 * ⚡ AUTOMATIC URL INTERCEPTION - webNavigation API
 * 
 * This listener fires BEFORE any page loads, allowing us to:
 * 1. Intercept the URL
 * 2. Check against ML backend
 * 3. Redirect to warning page if phishing detected
 * 4. Block the phishing site from loading
 */
chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  // Only intercept main frame navigations (not iframes)
  if (details.frameId !== 0) return;
  
  const url = details.url;
  
  // Skip non-HTTP URLs and extension pages
  if (!url.startsWith('http://') && !url.startsWith('https://')) return;
  if (url.includes('chrome-extension://')) return;
  if (url.includes('localhost:5000')) return; // Skip Flask backend
  
  // Skip trusted domains (Google, Facebook, Microsoft, etc.)
  if (isTrustedDomain(url)) {
    log('TRUSTED', `✅ Trusted domain, skipping check: ${url}`);
    return;
  }
  
  log('INTERCEPT', `🔍 Checking navigation to: ${url}`);

  // Heuristic short-circuit so warning shows BEFORE navigation
  const heuristic = getHeuristicRisk(url);
  if (heuristic.level === 'block' || heuristic.level === 'warn') {
    const heuristicConfidence = heuristic.level === 'block' ? 95 : 70;
    const heuristicCategory = heuristic.level === 'block' ? 'Heuristic High Risk' : 'Heuristic Suspicious';
    const warningUrl = chrome.runtime.getURL('warning.html') +
                      `?mode=${heuristic.level === 'block' ? 'block' : 'warn'}` +
                      `&url=${encodeURIComponent(url)}` +
                      `&confidence=${heuristicConfidence.toFixed(1)}` +
                      `&category=${encodeURIComponent(heuristicCategory)}`;

    log(heuristic.level === 'block' ? 'BLOCK' : 'WARN', `⚙️ Heuristic ${heuristic.level}: ${url}`, {
      score: heuristic.score,
      reasons: heuristic.reasons
    });

    chrome.tabs.update(details.tabId, { url: warningUrl });
    return;
  }

  // Get prediction from backend
  const prediction = await getPrediction(url);
  const backendConfidence = typeof prediction.probability === 'number' ? prediction.probability : 0;
  const backendCategory = prediction.risk_category || 'Unknown';
  const backendFailed = Boolean(prediction.error);

  let effectiveConfidence = backendConfidence;
  let effectiveCategory = backendCategory;

  if (backendFailed) {
    effectiveConfidence = Math.max(effectiveConfidence, 0.70);
    effectiveCategory = 'Temporary Risk (Backend Unavailable)';
  }

  // Determine action based on effective confidence
  const confidence = effectiveConfidence;
  
  if (confidence >= PHISHING_BLOCK_THRESHOLD) {
    // HIGH RISK - BLOCK COMPLETELY
    log('BLOCK', `🚫 BLOCKED phishing site: ${url}`, {
      confidence: `${(confidence * 100).toFixed(1)}%`,
      category: effectiveCategory
    });
    
    // Redirect to warning page
    const warningUrl = chrome.runtime.getURL('warning.html') + 
                      `?url=${encodeURIComponent(url)}` +
                      `&confidence=${(confidence * 100).toFixed(1)}` +
                      `&category=${encodeURIComponent(effectiveCategory)}`;
    
    chrome.tabs.update(details.tabId, { url: warningUrl });
    
  } else if (confidence >= PHISHING_WARN_THRESHOLD) {
    // MEDIUM RISK - WARN USER
    log('WARN', `⚠️ Warning for suspicious site: ${url}`, {
      confidence: `${(confidence * 100).toFixed(1)}%`,
      category: effectiveCategory
    });

    // Redirect to warning page so user sees the warning before navigation
    const warningUrl = chrome.runtime.getURL('warning.html') +
                      `?mode=warn` +
                      `&url=${encodeURIComponent(url)}` +
                      `&confidence=${(confidence * 100).toFixed(1)}` +
                      `&category=${encodeURIComponent(effectiveCategory)}`;

    chrome.tabs.update(details.tabId, { url: warningUrl });
    
  } else {
    // LOW RISK - ALLOW
    log('ALLOW', `✅ Safe site: ${url}`, {
      confidence: `${(confidence * 100).toFixed(1)}%`
    });
  }
});

/**
 * Message handler - receives requests from content.js and popup.js
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'predict') {
    log('MESSAGE', `📨 Received prediction request for: ${request.url}`);
    
    // Get prediction from backend (async)
    getPrediction(request.url)
      .then(result => {
        sendResponse({
          success: true,
          data: result
        });
      })
      .catch(error => {
        sendResponse({
          success: false,
          error: error.message
        });
      });
    
    // Return true to indicate we'll send response asynchronously
    return true;
  } else if (request.action === 'log') {
    // For debugging from content scripts
    log('PAGE', request.message);
  }
});

/**
 * Tab update listener - log page loads
 */
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    log('TAB', `📄 Page loaded: ${tab.url}`);
  }
});

// Periodic cache cleanup
setInterval(() => {
  const now = Date.now();
  let cleaned = 0;
  
  for (const [key, value] of urlCache.entries()) {
    if (now - value.timestamp > CACHE_DURATION) {
      urlCache.delete(key);
      cleaned++;
    }
  }
  
  if (cleaned > 0) {
    log('CACHE', `🧹 Cleaned up ${cleaned} old cache entries`);
  }
}, 600000); // Every 10 minutes

// Log extension startup
log('STARTUP', '🔒 Phishing Detector Extension Started');
log('INFO', `Backend URL: ${BACKEND_URL}`);
log('INFO', `Block threshold: ${(PHISHING_BLOCK_THRESHOLD * 100)}%`);
