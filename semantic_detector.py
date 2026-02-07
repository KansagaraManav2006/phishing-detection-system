"""
Semantic and rule-based phishing detection features.

WHY THIS FILE?
==============
The RandomForest ML model is trained on 41 numeric features and achieves 96.68% accuracy.
However, it sometimes gives LOW confidence (51%) on OBVIOUS phishing URLs like:
    http://google.com.verify-user.ru/login

WHY? Because the ML model learns statistical patterns. An obvious red flag to humans
(like "google" AND "verify" AND ".ru" TLD together) might have low statistical weight
in the training data if those patterns appear in legitimate URLs separately.

The semantic detector uses HUMAN RULES to catch what ML misses:
- Brand impersonation: "google" in the subdomain
- Suspicious keywords: "verify", "login" suggest credential theft
- Dangerous TLDs: ".ru", ".cn" are high-risk regions
- Complex subdomains: 3+ dots suggests spoofing

By combining both approaches (ML + semantic rules), we catch:
✓ What ML catches: Statistical patterns from 247,950 URLs
✓ What semantic catches: Human-obvious red flags

Result: Obvious phishing goes from 51% → 100% confidence
"""
from __future__ import annotations

from typing import Dict, Tuple

__all__ = ["detect_semantic_phishing"]

# ===== Brand Names Commonly Impersonated =====
# WHY: Attackers fake popular brands to steal credentials/data
# These are the top targets based on phishing statistics
BRANDS = {
    "google", "facebook", "paypal", "amazon", "apple", "microsoft",
    "netflix", "adobe", "apple", "instagram", "whatsapp", "twitter",
    "linkedin", "github", "dropbox", "slack", "zoom", "ebay",
    "walmart", "target", "uber", "airbnb", "airbus", "airplane"
}

# ===== Suspicious Keywords =====
# WHY: These words indicate credential theft or phishing attempts
# Legitimate sites rarely use ALL of these together
SUSPICIOUS_KEYWORDS = {
    "verify",      # "Verify your account" → credential theft
    "confirm",     # "Confirm your identity" → credential theft
    "update",      # "Update payment info" → financial info theft
    "login",       # "Click to login" → phishing destination
    "signin",
    "password",    # "Reset password" → credential theft
    "account",
    "security",    # "Security alert" → social engineering
    "urgent",      # "Urgent action needed" → creates panic
    "action",
    "required",
    "alert",
    "click",
    "claim",
    "validate",    # "Validate information" → data harvest
    "authenticate",
    "suspend",     # "Account suspended" → urgency
    "limited",     # "Limited time offer" → urgency
    "restricted",
    "unusual",     # "Unusual activity" → creates fear
    "activity",
    "strange",
    "expire",      # "Expires soon" → urgency
    "expired",
    "renew"
}

# ===== High-Risk TLDs =====
# WHY: Certain TLDs are more commonly used by phishers or have weak governance
# These are geographically/less-regulated domains commonly abused for phishing
SUSPICIOUS_TLDS = {
    "ru",          # Russia - common phishing origin
    "cn",          # China - high phishing volume
    "tk", "ml",    # Free TLDs - no governance/verification
    "ga", "cf",    # Free TLDs
    "gq",          # Free TLD
    "work",        # Generic - often abused
    "review",      # Generic - often abused
    "info",        # Historically high phishing volume
    "biz",         # Business-generic - easily mimicked
    "zip",         # Unusual, suspicious
    "download",    # Suggests malware
    "top",         # Top-level, generic = suspicious
    "online",      # Vague, commonly abused
    "site",        # Too generic
    "website",     # Too generic
    "red",         # Unusual for legitimate
    "party",       # Unusual for legitimate
    "click",       # Suspicious, suspicious purpose
    "stream"       # Often used for malware
}

# ===== Safe/Trusted TLDs =====
# WHY: These TLDs have reputation and verification requirements
# They're safer than free/generic TLDs
TRUSTED_TLDS = {
    "com", "org", "gov", "edu", "net",  # Classic, established
    "co.uk", "de", "fr",                # Country codes with standards
    "ca", "au", "jp", "in", "br",       # Country codes with standards
    "mx", "it", "es", "nl"              # Country codes with standards
}


def detect_semantic_phishing(url: str) -> Dict[str, int | float]:
    """
    Detect phishing indicators using semantic/rule-based analysis.
    
    STRATEGY: Use HUMAN KNOWLEDGE and ATTACK PATTERNS to flag obvious phishing
    
    Instead of learning from data like ML, we use domain expertise:
    - Attackers impersonate brands (Google, PayPal, etc.)
    - Attackers use persuasive language (verify, confirm, urgent)
    - Attackers use risky TLDs (.ru, .cn, free .tk, .ml)
    - Attackers create complex subdomain structures
    
    Each indicator gets a score (0.0 = legitimate, 2.0 = highly phishing)
    Final semantic score = sum of all indicators, normalized to 0-1
    
    EXAMPLE: "http://google.com.verify-user.ru/login"
    ├─ Brand Impersonation: 2.0 (google in subdomain!)
    ├─ Suspicious Keywords: 1.0 (verify + login)
    ├─ Suspicious TLD: 1.5 (.ru is dangerous)
    ├─ Subdomain Complexity: 1.5 (4 dots = too many subdomains)
    └─ Total: 6.0 → Normalized: 1.0 (100% phishing)
    
    Returns:
        Dict with keys:
        - brand_impersonation: 0-2 (is a brand name spoofed?)
        - suspicious_keywords: 0-2 (how many phishing keywords?)
        - suspicious_tld: 0-1.5 (is the TLD risky?)
        - subdomain_impersonation: 0-1.5 (too many subdomains?)
        - entropy_score: 0-1.5 (unusually long URL?)
    """
    url_lower = url.lower()
    domain_part = url_lower.split("://")[-1].split("/")[0]  # Extract just the domain
    hostname = domain_part.split("@")[-1].split(":")[0]     # Remove credentials and port
    
    indicators = {
        "brand_impersonation": 0,
        "suspicious_keywords": 0,
        "suspicious_tld": 0,
        "subdomain_impersonation": 0,
        "entropy_score": 0,
    }
    
    # ===== 1. BRAND IMPERSONATION DETECTION =====
    # WHY: Attackers often use brand names in subdomains to trick users
    # Examples:
    #   Legit: accounts.google.com (Google's real site)
    #   Fake: google.attacker.com (Attacker spoofing Google)
    #
    # We check if a known brand appears in the first-level subdomain (likely spoofing)
    for brand in BRANDS:
        if brand in hostname:
            # Check if brand is in first subdomain (likely impersonation)
            subdomains = hostname.split(".")
            if brand in subdomains[0]:  # Found in first subdomain (most obvious spoofing)
                indicators["brand_impersonation"] = 2  # HIGH confidence phishing
            else:
                indicators["brand_impersonation"] = 1  # Moderate
            break
    
    # ===== 2. SUSPICIOUS KEYWORDS DETECTION =====
    # WHY: Phishing pages use specific keywords to steal information:
    #   - "verify" → Steal credentials by making user re-enter them
    #   - "login" → Lead to fake login form
    #   - "confirm" → Social engineering for sensitive data
    #   - "urgent" → Create panic to bypass skepticism
    #
    # We count how many of these keywords appear in the entire URL
    # (More keywords = higher phishing likelihood)
    suspicious_count = sum(1 for keyword in SUSPICIOUS_KEYWORDS if keyword in url_lower)
    indicators["suspicious_keywords"] = min(suspicious_count * 0.5, 2.0)  # 0.5 per keyword, cap at 2.0
    
    # ===== 3. TLD (Top-Level Domain) ANALYSIS =====
    # WHY: Certain TLDs ("country codes") are more commonly abused:
    #   - .ru (Russia): High phishing volume
    #   - .cn (China): High phishing volume
    #   - .tk, .ml (Free TLDs): No verification, governance
    #   - .zip, .download: Unusual, suspicious purpose
    #
    # Legitimate companies use trusted TLDs (.com, .org, .edu)
    # Phishing often uses risky or free TLDs
    tld = hostname.split(".")[-1]  # Extract TLD (last part after final dot)
    if tld in SUSPICIOUS_TLDS:
        indicators["suspicious_tld"] = 1.5  # HIGH risk
    elif tld not in TRUSTED_TLDS:
        indicators["suspicious_tld"] = 0.5  # MEDIUM risk (unknown)
    
    # ===== 4. SUBDOMAIN IMPERSONATION DETECTION =====
    # WHY: Attackers use multiple subdomains to hide the real domain
    # Examples:
    #   Legit: www.google.com (2 dots = normal)
    #   Fake: google.attacker.com (3 dots = spoofing!)
    #   Super Fake: google.paypal.attacker.com (4 dots = obvious layering)
    #
    # The idea: legitimate companies don't need many subdomains
    # Phishers create fake "fake.real-brand.attacker.com" structures
    dot_count = hostname.count(".")
    if dot_count >= 3:
        indicators["subdomain_impersonation"] = 1.5  # 3+ dots = suspicious
    elif dot_count == 2:
        indicators["subdomain_impersonation"] = 0.5  # 2 dots = less suspicious
    
    # ===== 5. URL LENGTH ENTROPY =====
    # WHY: Phishing URLs are often:
    #   - VERY long (>75 chars): To hide suspicious intent in the URL
    #   - VERY short (but they're rare): Some obfuscation techniques use short URLs
    #   - Include hash/encoding: %xx, #, ; to obfuscate real destination
    if len(url) > 75:
        indicators["entropy_score"] = 1.0  # Unusually long
    elif len(url) > 100:
        indicators["entropy_score"] = 1.5  # VERY long, highly suspicious
    
    return indicators


def calculate_semantic_score(indicators: Dict[str, int | float]) -> float:
    """
    Calculate overall semantic phishing score (0-1).
    
    CONCEPT: Convert raw indicator scores into a single 0-1 score
    
    HOW IT WORKS:
    1. Add up all indicator scores (each 0-2)
    2. Maximum possible = ~6-7 points (if all indicators trigger)
    3. Normalize to 0-1 scale by dividing by 4.0
    4. Clamp between 0 and 1
    
    EXAMPLE: "google.com.verify-user.ru/login"
    └─ Indicators:
       ├─ brand_impersonation: 2.0
       ├─ suspicious_keywords: 1.0
       ├─ suspicious_tld: 1.5
       ├─ subdomain_impersonation: 1.5
       └─ entropy_score: 0.0
       └─ Total: 6.0
    
    └─ Normalization: 6.0 / 4.0 = 1.5 → capped at 1.0 → 100% semantic score
    
    INTERPRETATION:
    - 0.0-0.3: Legitimate (no suspicious patterns)
    - 0.3-0.6: Suspicious (some warning signs)
    - 0.6-0.8: Likely Phishing (multiple indicators triggered)
    - 0.8-1.0: High Confidence Phishing (many indicators triggered)
    """
    total_weight = sum(indicators.values())
    # Normalize to 0-1 range with aggressive weighting
    # Maximum possible indicators = 6.5, so divide by 4.0 to scale 0-1 range properly
    semantic_score = min(total_weight / 4.0, 1.0)  # Max 4 points possible → 1.0
    return semantic_score


def hybrid_prediction(model_probability: float, semantic_score: float) -> Tuple[float, str]:
    """
    Combine model probability with semantic score for better detection.
    
    WHY HYBRID?
    ============
    Problem: ML alone gives 51% on obvious phishing
    Solution: Blend ML (statistical) + Semantic (rule-based) detection
    
    ARCHITECTURE:
    ┌─────────────────────────────────────────────┐
    │ ML-Based (40% weight)                       │
    │ └─ Learns from 247,950 training URLs        │
    │    Catches complex patterns                 │
    │    But misses obvious signals               │
    │                                             │
    │ Semantic-Based (60% weight)                 │
    │ └─ Human rules about attacks                │
    │    Catches obvious red flags                │
    │    But can't learn new patterns             │
    │                                             │
    │ Hybrid = Best of both                       │
    └─────────────────────────────────────────────┘
    
    WHY 40/60 SPLIT?
    ================
    - We weight semantic detection MORE because:
      1. When semantic rules trigger (brand+keyword+TLD), it's usually phishing
      2. ML alone gives low confidence on these obvious cases
      3. False positives are bad but false negatives are worse
    
    - The 40% for ML captures patterns the rules might miss
    
    ALGORITHM:
    1. Base Score = (ML_probability × 0.4) + (Semantic_score × 0.6)
    2. If semantic score is very high (>0.7), boost confidence by +0.2
       This gives semantic detection more authority when it's confident
    3. Clamp final score to 0-1 range
    
    EXAMPLE:
    ┌─────────────────────────────────────────────────────────────┐
    │ URL: "google.com.verify-user.ru/login"                     │
    ├─────────────────────────────────────────────────────────────┤
    │ ML Model says:        51.5% phishing (0.515)                │
    │ Semantic rules say:   100% phishing (1.0)                   │
    ├─────────────────────────────────────────────────────────────┤
    │ Step 1: Base blend                                          │
    │         (0.515 × 0.4) + (1.0 × 0.6) =                      │
    │         0.206 + 0.6 = 0.806                                 │
    │                                                             │
    │ Step 2: Semantic boost (1.0 > 0.7)                          │
    │         0.806 + 0.2 = 1.006                                 │
    │                                                             │
    │ Step 3: Clamp to 0-1                                        │
    │         min(1.006, 1.0) = 1.0                               │
    ├─────────────────────────────────────────────────────────────┤
    │ RESULT: 100% Confidence (from 51%)                          │
    └─────────────────────────────────────────────────────────────┘
    
    Args:
        model_probability: RandomForest model probability (0-1)
                          What ML learned from data
        semantic_score: Semantic rule-based score (0-1)
                       What rules detected
    
    Returns:
        (combined_probability, confidence_level tuple)
        - combined_probability: Final 0-1 score
        - confidence_level: Text description ("Very High Risk", etc.)
    """
    # STEP 1: Weighted combination
    # ML gets 40% weight, Semantic gets 60% weight
    combined = (model_probability * 0.4) + (semantic_score * 0.6)
    
    # STEP 2: Semantic boost
    # If semantic detection is very confident (>0.7), give it more authority
    # This means: "When our rules are sure, the prediction should be very sure"
    if semantic_score > 0.7:
        combined = min(combined + 0.2, 1.0)  # Add +0.2 but don't exceed 1.0
    
    # STEP 3: Determine confidence text label based on combined score
    # These thresholds determine what message we show the user
    if combined >= 0.8:
        confidence = "Very High Risk"  # 80%+ = Definitely phishing
    elif combined >= 0.6:
        confidence = "High Risk"        # 60-80% = Likely phishing
    elif combined >= 0.4:
        confidence = "Medium Risk"      # 40-60% = Uncertain
    else:
        confidence = "Low Risk"         # <40% = Probably legitimate
    
    return combined, confidence
