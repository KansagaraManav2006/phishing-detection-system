/**
 * Popup Script - Extension Icon Popup
 * 
 * Shows extension status and current page analysis when user clicks icon
 */

document.addEventListener('DOMContentLoaded', async () => {
  const contentDiv = document.getElementById('content');
  
  try {
    // Get current active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.startsWith('http')) {
      contentDiv.innerHTML = `
        <div class="status warning">
          <div class="status-icon">ℹ️</div>
          <div class="status-text">
            <strong>Not applicable</strong>
            <p>Extension only works on regular web pages.</p>
          </div>
        </div>
      `;
      return;
    }
    
    // Display current URL analysis
    displayPageAnalysis(tab.url, contentDiv);
    
  } catch (error) {
    contentDiv.innerHTML = `
      <div class="status error">
        <div class="status-icon">⚠️</div>
        <div class="status-text">
          <strong>Error</strong>
          <p>${error.message}</p>
        </div>
      </div>
    `;
  }
});

/**
 * Display analysis of current page URL
 */
async function displayPageAnalysis(url, container) {
  container.innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <p>Analyzing current page...</p>
    </div>
  `;
  
  try {
    // Check if extension context is still valid
    if (!chrome.runtime || !chrome.runtime.id) {
      container.innerHTML = `
        <div class="status error">
          <div class="status-icon">⚠️</div>
          <div class="status-text">
            <strong>Extension Reload Required</strong>
            <p>Please refresh this page for the extension to work properly.</p>
          </div>
        </div>
      `;
      return;
    }
    
    // Send request to background script for prediction
    chrome.runtime.sendMessage(
      { action: 'predict', url: url },
      (response) => {
        // Check for extension context error
        if (chrome.runtime.lastError) {
          container.innerHTML = `
            <div class="status error">
              <div class="status-icon">⚠️</div>
              <div class="status-text">
                <strong>Extension Error</strong>
                <p>${chrome.runtime.lastError.message}</p>
                <p style="font-size: 11px; margin-top: 8px;">Please refresh the page.</p>
              </div>
            </div>
          `;
          return;
        }
        
        if (!response || response.success === false) {
          container.innerHTML = `
            <div class="status error">
              <div class="status-icon">⚠️</div>
              <div class="status-text">
                <strong>Backend Unavailable</strong>
                <p>Make sure the Flask server is running on localhost:5000</p>
              </div>
            </div>
            <div class="info-section">
              <h3>Setup Instructions</h3>
              <p style="font-size: 12px; line-height: 1.5;">
                Run the backend server:
                <br><code style="background: #f5f5f5; padding: 4px 6px; font-size: 11px;">python flask_server.py</code>
              </p>
            </div>
          `;
          return;
        }
        
        const prediction = response.data;
        const confidence = (prediction.probability * 100).toFixed(1);
        
        // Determine severity
        let statusClass = '';
        let statusIcon = '';
        let statusMessage = '';
        
        if (prediction.probability >= 0.8) {
          statusClass = 'error';
          statusIcon = '🔴';
          statusMessage = 'High Risk - This page appears to be phishing';
        } else if (prediction.probability >= 0.6) {
          statusClass = 'warning';
          statusIcon = '🟠';
          statusMessage = 'Medium Risk - This page shows suspicious patterns';
        } else {
          statusClass = 'success';
          statusIcon = '🟢';
          statusMessage = 'Safe - This page appears legitimate';
        }
        
        // Wait with error class if not safe
        if (statusClass === '') statusClass = 'success';
        
        container.innerHTML = `
          <div class="status ${statusClass}">
            <div class="status-icon">${statusIcon}</div>
            <div class="status-text">
              <strong>Page Status</strong>
              <p>${statusMessage}</p>
            </div>
          </div>
          
          <div class="info-section">
            <h3>Analysis Details</h3>
            <div class="info-item">
              <span class="info-label">Risk Level</span>
              <span class="info-value">${prediction.risk_category}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Phishing Confidence</span>
              <span class="info-value">${confidence}%</span>
            </div>
          </div>
          
          <div class="info-section">
            <h3>Current Page</h3>
            <div style="font-size: 12px; word-break: break-all; color: #666;">
              <code>${url}</code>
            </div>
          </div>
          
          <div class="actions">
            <button class="btn btn-secondary" onclick="window.close()">Close</button>
            <button class="btn btn-primary" onclick="openDetails()">Details</button>
          </div>
        `;
      }
    );
    
  } catch (error) {
    container.innerHTML = `
      <div class="status error">
        <div class="status-icon">❌</div>
        <div class="status-text">
          <strong>Error</strong>
          <p>${error.message}</p>
        </div>
      </div>
    `;
  }
}

/**
 * Open detailed analysis options
 */
function openDetails() {
  chrome.runtime.openOptionsPage?.() || 
  chrome.tabs.create({ url: 'popup.html?detailed=true' });
}
