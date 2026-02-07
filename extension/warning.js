const params = new URLSearchParams(window.location.search);
const blockedUrl = params.get('url') || 'Unknown';
const mode = params.get('mode') || 'block';
const confidenceParam = params.get('confidence');
const categoryParam = params.get('category');

const confidenceValue = Number.isFinite(parseFloat(confidenceParam))
  ? Math.min(100, Math.max(0, parseFloat(confidenceParam)))
  : 0;

document.getElementById('blockedUrl').textContent = decodeURIComponent(blockedUrl);
document.getElementById('confidence').textContent = `${confidenceValue.toFixed(1)}%`;
document.getElementById('category').textContent = categoryParam || 'High Risk Phishing';
document.getElementById('timestamp').textContent = new Date().toLocaleTimeString();

const confidenceBar = document.getElementById('confidenceBar');
requestAnimationFrame(() => {
  confidenceBar.style.width = `${confidenceValue}%`;
});

const goBackBtn = document.getElementById('goBackBtn');
const proceedBtn = document.getElementById('proceedBtn');
const warningHeader = document.getElementById('warningHeader');
const warningTitle = document.getElementById('warningTitle');
const warningSubtitle = document.getElementById('warningSubtitle');
const warningAlert = document.getElementById('warningAlert');

if (mode === 'block') {
  if (warningHeader) {
    warningHeader.classList.remove('warn');
    warningHeader.classList.add('block');
  }
  if (warningTitle) warningTitle.textContent = 'Phishing Link Blocked';
  if (warningSubtitle) warningSubtitle.textContent = 'This destination appears unsafe and may steal sensitive data.';
  if (warningAlert) {
    warningAlert.textContent = 'This link was blocked for your safety. Only proceed if you fully trust the source.';
  }
}

if (goBackBtn) {
  goBackBtn.addEventListener('click', () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = 'https://www.google.com';
    }
  });
}

if (proceedBtn) {
  proceedBtn.addEventListener('click', () => {
    const promptText = mode === 'warn'
      ? 'This link looks suspicious.\n\nDo you want to continue?'
      : 'Final warning. This page was flagged as risky.\n\nDo you still want to continue?';

    const confirmed = confirm(promptText);

    if (confirmed) {
      window.location.href = decodeURIComponent(blockedUrl);
    }
  });
}

if (chrome?.runtime?.sendMessage) {
  chrome.runtime.sendMessage({
    action: 'log',
    message: `User viewing warning page for: ${blockedUrl}`
  });
}
