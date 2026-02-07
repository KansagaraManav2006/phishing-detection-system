"""
Streamlit application for phishing website detection.

WHY STREAMLIT?
==============
Streamlit is a Python framework for building data apps without needing HTML/CSS/JavaScript.

Benefits:
1. FAST DEVELOPMENT: No frontend knowledge needed, pure Python
2. REAL-TIME UPDATES: Instant feedback as user types/submits
3. BEAUTIFUL UI: Professional-looking layouts with just Python functions
4. INTERACTIVITY: Buttons, text inputs, expandable sections all in Python
5. DEPLOYMENT: One-command deployment to cloud

Our app uses Streamlit to create:
- Text input field for URLs
- Analysis button to trigger prediction
- Color-coded results (🟢 green for safe, 🔴 red for phishing)
- Expandable details section showing feature analysis
- Real-time confidence metrics

TRADITIONAL APPROACH (Without Streamlit):
You'd need: Python backend + HTML + CSS + JavaScript + REST API
File structure:
  ├─ app.py (Flask/Django backend)
  ├─ templates/
  │  └─ index.html
  ├─ static/
  │  ├─ style.css
  │  └─ script.js
  └─ requirements.txt

STREAMLIT APPROACH (What we use):
Just: app.py (everything in Python)

Result: 10x faster development, 90% less code, same functionality!
"""
from __future__ import annotations

import streamlit as st

from feature_extractor import extract_features_from_url
from predict import predict_url


def main() -> None:
    """
    Main Streamlit app function.
    
    Streamlit automatically re-runs this function whenever:
    - User clicks a button
    - User types in a text field
    - State changes
    
    This reactive model makes building interactive apps trivial.
    """
    # PAGE CONFIGURATION
    # WHY: Set the browser tab title, icon, and layout
    st.set_page_config(
        page_title="Phishing Website Detection System",  # Browser tab title
        page_icon="🔒",                                  # Browser tab icon
        layout="wide"                                    # Use full width
    )
    
    # HEADER & DESCRIPTION
    # WHY: Tell users what this app does
    st.title("🔒 Phishing Website Detection System")
    st.markdown("### Analyze URLs to detect potential phishing threats")
    st.divider()

    # INPUT FIELD
    # WHY: Get URL from user
    url_input = st.text_input(
        "🌐 Enter Website URL",                             # Label
        placeholder="https://example.com",                  # Hint text
        help="Enter the full URL including http:// or https://"
    )

    # ANALYSIS BUTTON
    # WHY: Trigger prediction when clicked
    # type="primary" makes it blue and prominent
    # use_container_width=True makes it stretch across the page
    if st.button("🔍 Analyze URL", type="primary", use_container_width=True):
        if not url_input.strip():
            st.warning("⚠️ Please enter a URL before submitting.")
            return

        try:
            # PREDICTION PHASE
            # WHY: Call our ML/semantic hybrid prediction system
            label, probability, risk_category = predict_url(url_input)
            features = extract_features_from_url(url_input)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            st.error(f"❌ Analysis failed: {exc}")
            return

        # RESULT DETERMINATION
        # WHY: Convert label (0/1) to readable text
        prediction = "Phishing" if label == 1 else "Legitimate"
        
        # RESULT DISPLAY - 3 COLUMN LAYOUT
        # WHY: Show main prediction + confidence + risk in parallel for easy scanning
        col1, col2, col3 = st.columns(3)
        
        # COLUMN 1: Prediction Result
        # WHY: Show whether it's phishing or legitimate with color coding
        # Red error box for phishing (urgent!) vs Green success box for legitimate
        with col1:
            if prediction == "Phishing":
                st.error(f"### 🚨 {prediction}")  # Red background = danger
            else:
                st.success(f"### ✅ {prediction}")  # Green background = safe
        
        # COLUMN 2: Confidence Metric with Risk Status
        # WHY: Show confidence percentage with color-coded delta
        # Using metric widget shows number prominently with trend indicator
        with col2:
            prob_percent = probability * 100
            if prob_percent >= 70:
                # High phishing confidence: Red warning
                st.metric("⚠️ Confidence", f"{prob_percent:.1f}%", delta="High Risk", delta_color="inverse")
            elif prob_percent >= 50:
                # Medium phishing confidence: Orange warning
                st.metric("⚡ Confidence", f"{prob_percent:.1f}%", delta="Medium Risk", delta_color="off")
            else:
                # Low phishing confidence: Green safe
                st.metric("✓ Confidence", f"{prob_percent:.1f}%", delta="Low Risk", delta_color="normal")
        
        # COLUMN 3: Risk Category with Emoji Indicator
        # WHY: Visual indicator makes it easy to understand risk at a glance
        # 🟢 = Safe, 🟡 = Suspicious, 🟠 = Likely Phishing, 🔴 = High Risk
        with col3:
            # Map risk categories to emojis
            risk_emoji = {
                "Safe": "🟢",
                "Suspicious": "🟡", 
                "Likely Phishing": "🟠",
                "High Risk Phishing": "🔴"
            }
            emoji = risk_emoji.get(risk_category, "⚪")
            st.metric("📊 Risk Level", f"{emoji} {risk_category}")
        
        st.divider()
        
        # DETAILED ANALYSIS SECTION
        # WHY: Users want to understand WHY the system made this prediction
        # We show: suspicious patterns detected, feature metrics
        st.markdown("### 🔍 Analysis Details")
        
        # EXPANDABLE SECTION
        # WHY: By default hidden to keep UI clean, but available for curious users
        # Users can click to see technical details
        with st.expander("📈 Extracted Features", expanded=False):
            suspicious_features = []
            
            # CHECK FOR SUSPICIOUS PATTERNS IN FEATURES
            # WHY: Identify which specific URL characteristics triggered the alarm
            
            # Pattern 1: Multiple Subdomains
            # WHY: fake.google.attacker.com has 3 dots = domain spoofing
            if features.iloc[0]['number_of_dots_in_domain'] >= 3:
                suspicious_features.append(f"🔴 Multiple subdomains detected ({int(features.iloc[0]['number_of_dots_in_domain'])} dots in domain)")
            
            # Pattern 2: Hyphen in Domain
            # WHY: goog-le.com vs google.com - typosquatting uses hyphens
            if features.iloc[0]['number_of_hyphens_in_domain'] > 0:
                suspicious_features.append(f"🔴 Hyphen in domain (typosquatting indicator)")
            
            # Pattern 3: URL Too Long
            # WHY: Phishers hide bad intent in long URLs
            if features.iloc[0]['url_length'] > 75:
                suspicious_features.append(f"🔴 Unusually long URL ({int(features.iloc[0]['url_length'])} characters)")
            
            # Pattern 4: Multiple Subdomains (feature-based)
            # WHY: Legitimate sites have www or api, phishing has more layers
            if features.iloc[0]['number_of_subdomains'] >= 2:
                suspicious_features.append(f"🟡 Multiple subdomains ({int(features.iloc[0]['number_of_subdomains'])})")
            
            # Pattern 5: Suspicious Domain Structure
            # WHY: Missing path + multiple dots = likely domain spoofing
            if features.iloc[0]['having_path'] == 0 and features.iloc[0]['number_of_dots_in_domain'] >= 2:
                suspicious_features.append("🟡 Suspicious domain structure")
            
            # Pattern 6: High Entropy (Randomness)
            # WHY: Legitimate domains are branded/readable (low entropy)
            #      Phishing often uses random-looking parts (high entropy)
            if features.iloc[0]['entropy_of_url'] > 4.5:
                suspicious_features.append(f"🟡 High URL entropy ({features.iloc[0]['entropy_of_url']:.2f} - randomness detected)")
            
            # DISPLAY FINDINGS
            if suspicious_features:
                st.markdown("**⚠️ Suspicious Indicators Found:**")
                for feature in suspicious_features:
                    st.markdown(f"- {feature}")
            else:
                st.success("✅ No obvious suspicious indicators detected")
            
            # DISPLAY KEY METRICS
            # WHY: Show actual feature values so users understand the analysis
            st.markdown("**📊 Key Metrics:**")
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("URL Length", int(features.iloc[0]['url_length']),
                         help="Number of characters in URL. Phishing often >75")
            with col_b:
                st.metric("Domain Dots", int(features.iloc[0]['number_of_dots_in_domain']),
                         help="Number of subdomains. Phishing often ≥3")
            with col_c:
                st.metric("Subdomains", int(features.iloc[0]['number_of_subdomains']),
                         help="Count of subdomains. Phishing often >1")
            with col_d:
                st.metric("URL Entropy", f"{features.iloc[0]['entropy_of_url']:.2f}",
                         help="Randomness (0-8). Phishing often >4.5")
        
        # CONFIDENCE EXPLANATION
        # WHY: Educate users about why confidence might be moderate on phishing
        if prediction == "Phishing" and probability < 0.7:
            st.info("""
            ℹ️ **About Confidence Levels:** This URL shows phishing characteristics but with moderate confidence. 
            The model detects suspicious patterns (multiple subdomains, hyphens, domain structure) but the overall 
            feature profile doesn't strongly match extreme phishing patterns in the training data. Always exercise 
            caution with suspicious URLs regardless of confidence level.
            """)


if __name__ == "__main__":
    main()
