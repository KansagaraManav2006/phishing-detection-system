"""
Feature engineering utilities aligned with the Mendeley phishing dataset.

WHY THIS FILE?
==============
Machine learning models can't directly understand URLs as text strings. They need numeric features
(numbers) to learn patterns from. This file converts a URL into 41 carefully engineered numeric features
that capture different aspects of URL structure and complexity.

WHY 41 FEATURES?
================
The Mendeley phishing dataset was created by researchers who studied 247,950 phishing URLs and
identified which structural characteristics differentiate phishing URLs from legitimate ones.
The 41 features they engineered capture:
  1. URL complexity (length, dots, special characters)
  2. Domain characteristics (subdomains, hyphens, digits)
  3. Suspicious patterns (repeated digits, entropy)
  4. Path/query characteristics (presence, length)

These features work better than raw text because they're domain-specific - they target
the actual patterns attackers use (e.g., longer URLs, more subdomains, suspicious characters).

WHY THESE SPECIFIC FEATURES?
============================
Each feature serves a purpose based on phishing attack patterns:
  • URL Length: Phishing URLs are often longer to hide malicious content
  • Dots in Domain: Multiple dots indicate subdomains (e.g., fake.google.com) 
  • Hyphens in Domain: Lookalike domains use hyphens (e.g., goog-le.com)
  • Special Characters: Phishing URLs often have unusual encoding (%xx, @, etc.)
  • Entropy: Random-looking URLs suggest automated generation or obfuscation
  • Repeated Digits: Common in phishing (123456) vs legitimate sites
  • Subdomains: Many subdomains suggest domain spoofing attempts

The RandomForest model learns which combinations of these 41 features best predict phishing.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, Iterable
from urllib.parse import SplitResult, urlsplit

import pandas as pd

__all__ = ["extract_features_from_url"]

_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")

# These 41 feature names MUST match exactly what the trained RandomForest model expects.
# If you add/remove features, you must retrain the model. These features are in a specific
# order because the model learned to recognize phishing based on this exact ordering.
_FEATURE_COLUMNS = [
    # ===== URL-Level Features (8 features) =====
    # WHY: Phishing URLs have distinct structural characteristics at the URL level
    "url_length",                           # Longer URLs hide suspicious intent
    "number_of_dots_in_url",                # More dots = more obfuscated
    "having_repeated_digits_in_url",        # Sequential numbers suggest randomness/encoding
    "number_of_digits_in_url",              # Digit count patterns differ
    "number_of_special_char_in_url",        # Special chars reveal encoding attempts
    "number_of_hyphens_in_url",             # Hyphens used in typosquatting
    "number_of_underline_in_url",           # Unusual in legitimate URLs
    "number_of_slash_in_url",               # Path depth varies by intent
    "number_of_questionmark_in_url",        # Query strings common in phishing
    "number_of_equal_in_url",               # Parameter encoding
    "number_of_at_in_url",                  # @ symbol used to hide domain
    "number_of_dollar_in_url",              # Variable encoding
    "number_of_exclamation_in_url",         # Urgency signals
    "number_of_hashtag_in_url",             # Fragment/anchor usage patterns
    "number_of_percent_in_url",             # URL encoding frequency
    
    # ===== Domain-Level Features (8 features) =====
    # WHY: The domain is where attackers hide their intent. Legitimate domains have patterns,
    #      phishing domains break those patterns (e.g., multiple subdomains, hyphens, digits)
    "domain_length",                        # Short domains are trusted; very long = suspicious
    "number_of_dots_in_domain",             # Number of subdomains (more dots = more suspicious)
    "number_of_hyphens_in_domain",          # Common typosquatting technique
    "having_special_characters_in_domain",  # Legitimate domains rarely have special chars
    "number_of_special_characters_in_domain",
    "having_digits_in_domain",              # Legitimate brands avoid digits in domain
    "number_of_digits_in_domain",           # Pure digit count
    "having_repeated_digits_in_domain",     # 111, 222, etc. patterns (suspicious)
    
    # ===== Subdomain-Level Features (10 features) =====
    # WHY: Subdomain spoofing is a key phishing technique (e.g., google.attacker.com)
    #      These features capture subdomain complexity and patterns
    "number_of_subdomains",                 # How many subdomains are there?
    "having_dot_in_subdomain",              # Do subdomains have dots? (unusual)
    "having_hyphen_in_subdomain",           # Hyphens in subdomains = typosquatting
    "average_subdomain_length",             # Very short/long subdomains = suspicious
    "average_number_of_dots_in_subdomain",  # Dots within subdomains
    "average_number_of_hyphens_in_subdomain",  # Hyphens within subdomains
    "having_special_characters_in_subdomain",
    "number_of_special_characters_in_subdomain",
    "having_digits_in_subdomain",           # Digits in subdomains = brand impersonation
    "number_of_digits_in_subdomain",
    "having_repeated_digits_in_subdomain",  # 111, 222 in subdomains
    
    # ===== Path & Query Features (5 features) =====
    # WHY: Phishing pages have specific path structures designed to redirect/collect data
    "having_path",                          # Legitimate sites often have paths; phishing may not
    "path_length",                          # Length of the path component
    "having_query",                         # Query strings for form data
    "having_fragment",                      # Fragment identifiers
    "having_anchor",                        # Anchor/bookmark usage (# character)
    
    # ===== Entropy Features (2 features) =====
    # WHY: Shannon entropy measures randomness. Phishing URLs are often randomly generated
    #      to evade filters, resulting in higher entropy than legitimate branded URLs
    "entropy_of_url",                       # Overall randomness/disorder in URL
    "entropy_of_domain",                    # Randomness in domain specifically
]


def _ensure_scheme(url: str) -> str:
    """Add http:// prefix if URL doesn't have a scheme.
    
    WHY: URLs must have a scheme (http://, https://, etc.) to be parsed correctly.
    Users often copy URLs without the scheme, so we add it to normalize input.
    """
    candidate = url.strip()
    if not candidate:
        raise ValueError("URL must be a non-empty string")
    if not _SCHEME_RE.match(candidate):
        candidate = f"http://{candidate}"
    return candidate


def _split_url_parts(url: str) -> SplitResult:
    """Parse URL into components (scheme, netloc, path, query, fragment).
    
    WHY: Python's urlsplit breaks a URL into logical parts so we can analyze
    each component separately. Example:
      http://user:pass@domain.com:8080/path?query=1#fragment
      ├─ scheme: http
      ├─ netloc: user:pass@domain.com:8080
      ├─ path: /path
      ├─ query: query=1
      └─ fragment: fragment
    """
    normalized = _ensure_scheme(url)
    return urlsplit(normalized)


def _safe_domain(parsed: SplitResult) -> str:
    """Extract just the hostname from a parsed URL, removing user/port info.
    
    WHY: URLs can contain user credentials (user@domain) and port numbers (:8080).
    We only care about the actual domain name for analysis. This also
    ensures we extract the real target domain.
    """
    host = parsed.netloc.split("@")[-1]  # Remove user:pass@ prefix if present
    host = host.split(":")[0]             # Remove :port number if present
    return host.lower()


def _count_special_characters(text: str) -> int:
    """Count non-alphanumeric characters.
    
    WHY: Phishing URLs often contain unusual encoding, obfuscation with special
    characters (@, %, $, etc.) to hide the real domain or add confusion.
    Legitimate sites keep URLs clean with minimal special characters.
    """
    return sum(1 for char in text if not char.isalnum())


def _has_repeated_digit(text: str) -> int:
    """Check if any digit appears multiple times in sequence/within text.
    
    WHY: Phishing URLs often contain repeated patterns like 111, 222, etc.
    This is often from automated URL generation or tries to look legitimate
    by padding numbers. Legitimate domains rarely have such patterns.
    """
    counts = Counter(char for char in text if char.isdigit())
    return int(any(count > 1 for count in counts.values()))


def _shannon_entropy(text: str) -> float:
    """Calculate Shannon entropy - measure of randomness in text.
    
    WHY: Shannon entropy quantifies how "random" or "unpredictable" text is:
    - Low entropy (near 1.0): Predictable, ordered text (e.g., "aaaaa")
    - High entropy (near 5.0+): Random text (e.g., "x7k9m2")
    
    Phishing URLs often contain random-looking subdomains, obfuscated domains,
    or hash-like strings, resulting in higher entropy than legitimate domains.
    Example:
      google.com → low entropy (predictable, branded)
      x7k9m2z1q4.tk → high entropy (random, suspicious)
    """
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def _subdomain_parts(domain: str) -> Iterable[str]:
    """Extract subdomains from a domain.
    
    WHY: A domain like "fake.google.attacker.com" has subdomains:
      - "attacker.com" is the actual registrar (TLD)
      - "google" is a fake subdomain (impersonation)
      - "fake" is another fake subdomain
    
    We extract everything except the last 2 parts (which are the actual
    registered domain and TLD). This helps detect domain spoofing.
    """
    parts = [segment for segment in domain.split(".") if segment]
    if len(parts) <= 2:
        return []
    return parts[:-2]  # Return all except last 2 (domain + TLD)


def _aggregate_subdomain_metrics(parts: Iterable[str]) -> Dict[str, float]:
    """Calculate statistics across all subdomains.
    
    WHY: Instead of just counting subdomains, we calculate their CHARACTERISTICS:
    - Average length: Legitimate subdomains have predictable lengths
    - Average hyphens: Legitimate subdomains rarely have many hyphens
    - Presence of digits: Phishing often puts digits in subdomains to fake legitimacy
    - Special characters: Used for obfuscation
    
    Example: fake.amazon.attacker.com
      Subdomains: ["fake", "amazon"]
      → average length = 5
      → average hyphens = 0
      → has digits = 0
      → has special chars = 0
    
    vs: fake-12.am@zon-5.attacker.com
      → average length = 11
      → average hyphens = 2
      → has digits = 1 (suspicious!)
      → has special chars = 1 (suspicious!)
    """
    parts = list(parts)
    if not parts:
        return {
            "count": 0,
            "avg_len": 0.0,
            "avg_dots": 0.0,
            "avg_hyphens": 0.0,
            "special_count": 0,
            "has_special": 0,
            "digit_count": 0,
            "has_digit": 0,
            "has_repeated_digit": 0,
            "has_dot": 0,
            "has_hyphen": 0,
        }

    total_len = sum(len(part) for part in parts)
    total_dots = sum(part.count(".") for part in parts)
    total_hyphens = sum(part.count("-") for part in parts)
    special_count = sum(_count_special_characters(part) for part in parts)
    digit_count = sum(char.isdigit() for part in parts for char in part)
    has_digit = int(digit_count > 0)
    has_repeated_digit = int(
        any(
            Counter(char for char in part if char.isdigit()).most_common(1)[0][1] > 1
            for part in parts
            if any(char.isdigit() for char in part)
        )
    )
    has_special = int(special_count > 0)
    has_dot = int(len(parts) > 1)
    has_hyphen = int(any("-" in part for part in parts))

    return {
        "count": len(parts),
        "avg_len": total_len / len(parts),
        "avg_dots": total_dots / len(parts),
        "avg_hyphens": total_hyphens / len(parts),
        "special_count": special_count,
        "has_special": has_special,
        "digit_count": digit_count,
        "has_digit": has_digit,
        "has_repeated_digit": has_repeated_digit,
        "has_dot": has_dot,
        "has_hyphen": has_hyphen,
    }


def extract_features_from_url(url: str) -> pd.DataFrame:
    """
    Convert a URL into 41 numeric features for ML prediction.
    
    WORKFLOW:
    1. Parse the URL into components (domain, path, query, etc.)
    2. Calculate metrics for each component
    3. Combine all metrics into a single dataframe row
    4. Return in the exact column order the RandomForest model expects
    
    WHY:
    The RandomForest model was trained on 247,950 URLs, each with 41 features.
    To predict on a new URL, we must extract the same 41 features in the same order.
    If we change the feature order or add/remove features, the model will fail.
    
    INPUT: "http://google.com.verify-user.ru/login"
    
    EXTRACTION PROCESS:
    ┌─ Parse URL
    │  ├─ scheme: http
    │  ├─ netloc: google.com.verify-user.ru
    │  ├─ path: /login
    │  ├─ query: (empty)
    │  └─ fragment: (empty)
    │
    ├─ URL-Level Metrics
    │  ├─ url_length: 45
    │  ├─ dots: 4
    │  ├─ special chars: 2 (dot, hyphen)
    │  └─ entropy: 4.2 (fairly random)
    │
    ├─ Domain Metrics (google.com.verify-user.ru)
    │  ├─ domain_length: 33
    │  ├─ dots: 3 (multiple subdomains!)
    │  ├─ hyphens: 1 (suspicious!)
    │  └─ entropy: 3.8
    │
    └─ Subdomain Metrics (verify-user | google)
       ├─ count: 2 subdomains
       ├─ avg length: 9
       └─ has_hyphen: 1 (suspicious!)
    
    OUTPUT: Pandas DataFrame with 1 row, 41 columns (all numeric)
    """
    parsed = _split_url_parts(url)
    normalized_url = parsed.geturl()
    domain = _safe_domain(parsed)

    url_length = len(normalized_url)
    number_of_dots_in_url = normalized_url.count(".")
    number_of_digits_in_url = sum(char.isdigit() for char in normalized_url)
    number_of_special_char_in_url = _count_special_characters(normalized_url)

    domain_special_count = _count_special_characters(domain)
    domain_digit_count = sum(char.isdigit() for char in domain)

    subdomain_metrics = _aggregate_subdomain_metrics(_subdomain_parts(domain))

    feature_values = {
        "url_length": url_length,
        "number_of_dots_in_url": number_of_dots_in_url,
        "having_repeated_digits_in_url": _has_repeated_digit(normalized_url),
        "number_of_digits_in_url": number_of_digits_in_url,
        "number_of_special_char_in_url": number_of_special_char_in_url,
        "number_of_hyphens_in_url": normalized_url.count("-"),
        "number_of_underline_in_url": normalized_url.count("_"),
        "number_of_slash_in_url": normalized_url.count("/"),
        "number_of_questionmark_in_url": normalized_url.count("?"),
        "number_of_equal_in_url": normalized_url.count("="),
        "number_of_at_in_url": normalized_url.count("@"),
        "number_of_dollar_in_url": normalized_url.count("$"),
        "number_of_exclamation_in_url": normalized_url.count("!"),
        "number_of_hashtag_in_url": normalized_url.count("#"),
        "number_of_percent_in_url": normalized_url.count("%"),
        "domain_length": len(domain),
        "number_of_dots_in_domain": domain.count("."),
        "number_of_hyphens_in_domain": domain.count("-"),
        "having_special_characters_in_domain": int(domain_special_count > 0),
        "number_of_special_characters_in_domain": domain_special_count,
        "having_digits_in_domain": int(domain_digit_count > 0),
        "number_of_digits_in_domain": domain_digit_count,
        "having_repeated_digits_in_domain": _has_repeated_digit(domain),
        "number_of_subdomains": subdomain_metrics["count"],
        "having_dot_in_subdomain": subdomain_metrics["has_dot"],
        "having_hyphen_in_subdomain": subdomain_metrics["has_hyphen"],
        "average_subdomain_length": subdomain_metrics["avg_len"],
        "average_number_of_dots_in_subdomain": subdomain_metrics["avg_dots"],
        "average_number_of_hyphens_in_subdomain": subdomain_metrics["avg_hyphens"],
        "having_special_characters_in_subdomain": subdomain_metrics["has_special"],
        "number_of_special_characters_in_subdomain": subdomain_metrics["special_count"],
        "having_digits_in_subdomain": subdomain_metrics["has_digit"],
        "number_of_digits_in_subdomain": subdomain_metrics["digit_count"],
        "having_repeated_digits_in_subdomain": subdomain_metrics["has_repeated_digit"],
        "having_path": int(bool(parsed.path and parsed.path != "/")),
        "path_length": len(parsed.path),
        "having_query": int(bool(parsed.query)),
        "having_fragment": int(bool(parsed.fragment)),
        "having_anchor": int("#" in normalized_url),
        "entropy_of_url": _shannon_entropy(normalized_url),
        "entropy_of_domain": _shannon_entropy(domain),
    }

    dataframe = pd.DataFrame([feature_values])
    return dataframe[_FEATURE_COLUMNS]
