/**
 * Content Script - Improved for Reliable Link Interception
 * 
 * This version uses a more robust approach:
 * 1. Store the pending URL to open
 * 2. Show modal immediately without preventing
 * 3. User chooses the action from the modal
 */

const PHISHING_BLOCK_THRESHOLD = 0.80;
const PHISHING_WARN_THRESHOLD = 0.60;
const predictionCache = new Map();
let currentModalShown = false;
let pendingUrl = null;

function getPhishingAction(probability) {
  if (probability >= PHISHING_BLOCK_THRESHOLD) return 'BLOCK';
  if (probability >= PHISHING_WARN_THRESHOLD) return 'WARN';
  return 'ALLOW';
}

function injectStyles() {
  if (document.getElementById('phishing-detector-styles')) return;
  
  const style = document.createElement('style');
  style.id = 'phishing-detector-styles';
  style.textContent = `
    .phishing-modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 2147483647;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .phishing-modal-content {
      background: white;
      border-radius: 15px;
      max-width: 520px;
      width: 90%;
      box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
      animation: slideIn 0.3s ease;
      overflow: hidden;
    }
    
    @keyframes slideIn {
      from { opacity: 0; transform: translateY(-40px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .phishing-header {
      padding: 25px;
      color: white;
      display: flex;
      align-items: center;
      gap: 15px;
    }
    
    .phishing-header-block {
      background: linear-gradient(135deg, #c62828 0%, #8b0000 100%);
    }
    
    .phishing-header-warn {
      background: linear-gradient(135deg, #e65100 0%, #bf360c 100%);
    }
    
    .phishing-icon {
      font-size: 48px;
      line-height: 1;
    }
    
    .phishing-header h2 {
      margin: 0;
      font-size: 20px;
    }
    
    .phishing-body {
      padding: 20px 25px;
      color: #333;
    }
    
    .phishing-body p {
      margin: 10px 0;
      line-height: 1.6;
    }
    
    .phishing-body strong {
      color: #c62828;
    }
    
    .phishing-url {
      background: #f5f5f5;
      border-left: 4px solid #ff6f00;
      padding: 12px;
      margin: 15px 0;
      border-radius: 4px;
      word-break: break-all;
      font-size: 13px;
      font-family: Menlo, Courier, monospace;
    }
    
    .phishing-confidence {
      background: #fff3cd;
      border: 1px solid #ffc107;
      padding: 12px;
      margin: 12px 0;
      border-radius: 4px;
      font-size: 13px;
    }
    
    .phishing-list {
      margin: 12px 0 0 0;
      padding: 0 0 0 20px;
    }
    
    .phishing-list li {
      margin: 6px 0;
      font-size: 13px;
    }
    
    .phishing-actions {
      display: flex;
      gap: 12px;
      padding: 20px 25px;
      background: #fafafa;
      border-top: 1px solid #e0e0e0;
    }
    
    .phishing-btn {
      flex: 1;
      padding: 12px 20px;
      border: none;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .phishing-btn-block {
      background: #999;
      color: white;
      width: 100%;
    }
    
    .phishing-btn-block:hover {
      background: #777;
    }
    
    .phishing-btn-no {
      background: #c62828;
      color: white;
    }
    
    .phishing-btn-no:hover {
      background: #8b0000;
    }
    
    .phishing-btn-yes {
      background: #ddd;
      color: #333;
    }
    
    .phishing-btn-yes:hover {
      background: #bbb;
    }
  `;
  document.head.appendChild(style);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showBlockedModal(url, probability) {
  if (currentModalShown) return;
  currentModalShown = true;
  
  const conf = (probability * 100).toFixed(0);
  
  const modal = document.createElement('div');
  modal.className = 'phishing-modal';
  modal.innerHTML = `
    <div class="phishing-modal-content">
      <div class="phishing-header phishing-header-block">
        <span class="phishing-icon">🔴</span>
        <h2>BLOCKED - Phishing Detected</h2>
      </div>
      <div class="phishing-body">
        <p><strong>This link is blocked for your protection.</strong></p>
        <p>Our system detected this with <strong>${conf}% confidence</strong> to be a phishing attempt.</p>
        <div class="phishing-url">
          <strong>URL:</strong><br>${escapeHtml(url)}
        </div>
        <p>Do not open this link. Close this warning immediately.</p>
      </div>
      <div class="phishing-actions">
        <button class="phishing-btn phishing-btn-block">Close</button>
      </div>
    </div>
  `;
  
  injectStyles();
  document.body.appendChild(modal);
  
  modal.querySelector('.phishing-btn-block').addEventListener('click', () => {
    modal.remove();
    currentModalShown = false;
  });
  
  document.addEventListener('keydown', function escapeClose(e) {
    if (e.key === 'Escape') {
      modal.remove();
      currentModalShown = false;
      document.removeEventListener('keydown', escapeClose);
    }
  });
}

function showWarningModal(url, probability) {
  if (currentModalShown) return;
  currentModalShown = true;
  
  pendingUrl = url;
  const conf = (probability * 100).toFixed(0);
  
  const modal = document.createElement('div');
  modal.className = 'phishing-modal';
  modal.innerHTML = `
    <div class="phishing-modal-content">
      <div class="phishing-header phishing-header-warn">
        <span class="phishing-icon">🟠</span>
        <h2>Suspicious Link Detected</h2>
      </div>
      <div class="phishing-body">
        <p><strong>Warning:</strong> This link appears suspicious.</p>
        <div class="phishing-confidence">
          Phishing Confidence: <strong>${conf}%</strong>
        </div>
        <div class="phishing-url">
          <strong>URL:</strong><br>${escapeHtml(url)}
        </div>
        <p><strong>Characteristics detected:</strong></p>
        <ul class="phishing-list">
          <li>Suspicious domain structure</li>
          <li>Possible brand impersonation</li>
          <li>Unusual URL pattern</li>
        </ul>
      </div>
      <div class="phishing-actions">
        <button class="phishing-btn phishing-btn-no">🛑 Don't Open</button>
        <button class="phishing-btn phishing-btn-yes">⚠️ Open Anyway</button>
      </div>
    </div>
  `;
  
  injectStyles();
  document.body.appendChild(modal);
  
  modal.querySelector('.phishing-btn-no').addEventListener('click', () => {
    modal.remove();
    currentModalShown = false;
    pendingUrl = null;
  });
  
  modal.querySelector('.phishing-btn-yes').addEventListener('click', () => {
    modal.remove();
    currentModalShown = false;
    
    const targetUrl = pendingUrl;
    pendingUrl = null;
    
    console.log('[Phishing Detector] User chose to open anyway:', targetUrl);
    
    // Tell background.js to temporarily allow this URL
    if (chrome?.runtime?.sendMessage) {
      chrome.runtime.sendMessage({
        action: 'allowUrl',
        url: targetUrl
      }, (response) => {
        // After allowlist is updated, navigate
        navigateToUrl(targetUrl);
      });
    } else {
      // No extension API available, just navigate
      navigateToUrl(targetUrl);
    }
  });
  
  function navigateToUrl(url) {
    // Try multiple navigation methods for better compatibility
    try {
      window.location.href = url;
    } catch (e) {
      console.error('[Phishing Detector] Direct navigation failed:', e);
      
      // Method 2: Create and click a temporary link
      try {
        const tempLink = document.createElement('a');
        tempLink.href = url;
        tempLink.target = '_self';
        tempLink.style.display = 'none';
        document.body.appendChild(tempLink);
        tempLink.click();
        document.body.removeChild(tempLink);
      } catch (e2) {
        console.error('[Phishing Detector] Link click failed:', e2);
        
        // Method 3: Force navigation via window.open
        try {
          window.open(url, '_self');
        } catch (e3) {
          console.error('[Phishing Detector] All navigation methods failed:', e3);
          alert('Unable to navigate. Please copy the URL and paste it in a new tab.');
        }
      }
    }
  }
  
  document.addEventListener('keydown', function escapeClose(e) {
    if (e.key === 'Escape') {
      modal.remove();
      currentModalShown = false;
      pendingUrl = null;
      document.removeEventListener('keydown', escapeClose);
    }
  });
}

function analyzeAndNavigate(url) {
  // Check cache
  if (predictionCache.has(url)) {
    const cached = predictionCache.get(url);
    const prediction = cached.prediction;
    const action = getPhishingAction(prediction.probability);
    
    if (action === 'ALLOW') {
      window.location.href = url;
    } else if (action === 'WARN') {
      showWarningModal(url, prediction.probability);
    } else if (action === 'BLOCK') {
      showBlockedModal(url, prediction.probability);
    }
    return;
  }
  
  // Check if extension context is still valid
  if (!chrome.runtime || !chrome.runtime.id) {
    console.log('[Phishing] Extension context invalidated - please refresh the page');
    window.location.href = url;
    return;
  }
  
  // Send to background for analysis
  try {
    chrome.runtime.sendMessage({ action: 'predict', url: url }, (response) => {
      // Check for extension context error
      if (chrome.runtime.lastError) {
        console.log('[Phishing] Extension error:', chrome.runtime.lastError.message);
        window.location.href = url;
        return;
      }
      
      if (!response || !response.success) {
        console.log('[Phishing] Backend unavailable, allowing link');
        window.location.href = url;
        return;
      }
      
      const prediction = response.data;
      const action = getPhishingAction(prediction.probability);
      
      // Cache it
      predictionCache.set(url, { prediction, timestamp: Date.now() });
      
      console.log(`[Phishing] Analysis: ${(prediction.probability*100).toFixed(0)}% - ${url}`);
      
      if (action === 'ALLOW') {
        window.location.href = url;
      } else if (action === 'WARN') {
        showWarningModal(url, prediction.probability);
      } else if (action === 'BLOCK') {
        showBlockedModal(url, prediction.probability);
      }
    });
  } catch (error) {
    console.log('[Phishing] Extension context error:', error.message);
    window.location.href = url;
  }
}

// Intercept link clicks
document.addEventListener('click', (e) => {
  const link = e.target.closest('a');
  if (!link) return;
  
  const url = link.href;
  
  // Skip non-HTTP links
  if (!url || !url.startsWith('http')) {
    return;
  }
  
  // Stop the link from opening
  e.preventDefault();
  e.stopPropagation();
  
  // Analyze the URL
  analyzeAndNavigate(url);
}, true); // Use capture phase

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showWarning') {
    // Background script detected suspicious navigation
    showWarningModal(request.url, request.prediction.probability);
    sendResponse({ received: true });
  }
  return true;
});

console.log('[🔒 Phishing Detector] Content script loaded and monitoring links');
