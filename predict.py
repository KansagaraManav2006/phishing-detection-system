"""
Utilities for loading phishing detection artifacts and scoring URLs.

OVERALL ARCHITECTURE
====================

This module is the CENTRAL HUB that combines everything:

    Input URL
        ↓
    [predict_url()]
        ├─ Load RandomForest model (trained on 247,950 URLs)
        ├─ Extract 41 features from URL
        ├─ Get ML probability (0-1)
        ├─ Get semantic score (0-1)
        └─ Combine both → Final prediction
        ↓
    Output: (label, probability, risk_category)

WHY THIS DESIGN?
================
1. SEPARATION OF CONCERNS:
   - feature_extractor.py: Just extracts features
   - semantic_detector.py: Just evaluates rules
   - predict.py: Orchestrates both
   - app.py: Just displays results
   
   Each file has ONE job, making it maintainable

2. REUSABILITY:
   - App can use predict_url() without knowing about features
   - predict.py can use feature extraction independently
   - semantic detection can be tested separately
   
3. DEBUGGING:
   - Issue with predictions? Check predict.py
   - Issue with features? Check feature_extractor.py
   - Issue with rules? Check semantic_detector.py

DATA FLOW THROUGH PREDICT.PY
============================

Input: "http://google.com.verify-user.ru/login"
       ↓
1. _load_artifacts()
   ├─ Load model.pkl containing:
   │  ├─ RandomForest (trained model)
   │  └─ feature_columns (list of 41 expected feature names)
   └─ Return model, feature_columns

2. extract_features_from_url()
   └─ Return DataFrame with 41 numeric columns
      ├─ url_length: 45
      ├─ number_of_dots_in_url: 4
      ├─ ... (38 more features)
      └─ entropy_of_domain: 3.8

3. model.predict_proba(features)
   └─ RandomForest outputs probabilities for each class
      ├─ Class 0 (Legitimate): 0.485 (48.5%)
      └─ Class 1 (Phishing): 0.515 (51.5%)

4. semantic_detector.detect_semantic_phishing()
   └─ Analyzes same URL with RULES
      ├─ Brand impersonation: 2.0 (google found!)
      ├─ Suspicious keywords: 1.0 (verify + login)
      ├─ Suspicious TLD: 1.5 (.ru is risky)
      ├─ Subdomain complexity: 1.5 (4 dots)
      └─ Semantic score: 1.0 (100%)

5. hybrid_prediction(0.515, 1.0)
   └─ Combine ML + Semantic
      ├─ Base: (0.515 × 0.4) + (1.0 × 0.6) = 0.806
      ├─ Semantic boost: 0.806 + 0.2 = 1.006
      └─ Final: min(1.006, 1.0) = 1.0 (100%)

Output: (1, 1.0, "High Risk Phishing")
        (phishing, 100% confidence, risk category)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib

from feature_extractor import extract_features_from_url
from semantic_detector import detect_semantic_phishing, calculate_semantic_score, hybrid_prediction

# WHERE IS THE MODEL STORED?
# WHY: Models take time to train, so we store them as files
# Once trained, we just load the saved model for predictions (< 100ms)
_MODEL_PATH = Path(__file__).resolve().parent / "model" / "model.pkl"

# GLOBAL CACHE: Keep model in memory after first load
# WHY: Loading from disk is slow (~1 second). Users may submit multiple URLs
# so we cache the model after first load for instant predictions
_MODEL = None
_FEATURE_COLUMNS: Optional[List[str]] = None


def _load_artifacts() -> Tuple[object, List[str]]:
    """
    Load the trained RandomForest model and expected feature columns.
    
    WHY SEPARATE LOADING FUNCTION?
    ==============================
    1. LAZY LOADING: Only load if we need to predict
       - If app starts but user doesn't submit URL, we don't waste time loading
       - First prediction is slightly slow, rest are fast
    
    2. ERROR CHECKING: Validate before using
       - Check model file exists
       - Check model has predict_proba() method
       - Check feature columns match expectations
       - Clear error messages if something's wrong

    3. CACHING: Keep loaded model in memory
       - Global variables _MODEL and _FEATURE_COLUMNS store loaded data
       - Second prediction uses cached model (no disk read)
    
    WHAT DOES model.pkl CONTAIN?
    ============================
    A Python dictionary saved with joblib:
    {
        "model": <RandomForestClassifier object>,  # Trained on 247,950 URLs
                                                    # 200 decision trees
                                                    # 96.68% test accuracy
        "feature_columns": [                        # List of 41 column names
            "url_length",
            "number_of_dots_in_url",
            ...
            "entropy_of_domain"
        ]
    }
    
    WHY SAVE FEATURE COLUMNS IN THE MODEL?
    ======================================
    The model expects features in a SPECIFIC ORDER:
    
    Training:
      DataFrame columns: [url_length, dots, hyphens, ..., entropy]
      Model learned: "Feature at position 0 is important", etc.
    
    Prediction with wrong order:
      DataFrame columns: [entropy, ..., url_length, dots, hyphens]
      Model gets: Different feature at position 0!
      Result: WRONG PREDICTION (garbage in, garbage out)
    
    By storing feature_columns in model.pkl, we ensure:
    1. Reindex features to match training order before prediction
    2. Detect if feature extractor has a bug (missing/extra columns)
    """
    global _MODEL, _FEATURE_COLUMNS

    if _MODEL is None or _FEATURE_COLUMNS is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Missing trained model at {_MODEL_PATH}. Run the training notebook to generate it."
            )

        # LOAD FROM DISK
        artifact = joblib.load(_MODEL_PATH)

        if isinstance(artifact, dict):
            # NEW FORMAT: Dictionary with metadata
            _MODEL = artifact.get("model")
            _FEATURE_COLUMNS = artifact.get("feature_columns")
            if _MODEL is None or _FEATURE_COLUMNS is None:
                raise KeyError(
                    "Model artifact must include 'model' and 'feature_columns'. Re-run training.ipynb."
                )
        else:
            # OLD FORMAT: Just the model (for backwards compatibility)
            _MODEL = artifact
            if hasattr(_MODEL, "feature_columns_"):
                _FEATURE_COLUMNS = list(getattr(_MODEL, "feature_columns_"))
            else:
                raise AttributeError(
                    "Loaded model is missing feature metadata. Retrain to store feature_columns."
                )

        # VALIDATION: Is this actually a RandomForest we can use?
        if not hasattr(_MODEL, "predict_proba"):
            raise AttributeError("Loaded model lacks predict_proba(). Train with RandomForestClassifier.")

    if _FEATURE_COLUMNS is None:
        raise RuntimeError("Failed to load feature column metadata from the model artifact.")

    return _MODEL, list(_FEATURE_COLUMNS)


def _resolve_phishing_probability(probabilities, classes) -> float:
    """
    Extract the probability of the PHISHING class from model output.
    
    WHY IS THIS NEEDED?
    ===================
    RandomForest returns probabilities for ALL classes:
    
    model.predict_proba(features) → [prob_class_0, prob_class_1, ...]
    
    We trained the model with classes [0, 1]:
    - Class 0 = Legitimate (48.5%)
    - Class 1 = Phishing (51.5%)
    
    But we need to FIND which index is "phishing" class because:
    1. Different datasets might use different labels (0/1 vs 1/2 vs "phishing"/"legitimate")
    2. We want to be flexible to changing labels
    3. We must return only the PHISHING probability, not legitimate
    
    ALGORITHM:
    1. Try to find class 1 (standard phishing label)
    2. If not found, search by name in ["phishing", "malicious", "fraud", ...]
    3. Return the probability at that class index
    4. Raise error if class not found
    """
    class_list = list(classes)

    # ATTEMPT 1: Standard label (1 = phishing)
    if 1 in class_list:
        index = class_list.index(1)
        return float(probabilities[index])

    # ATTEMPT 2: Search by name
    normalized = [str(cls).strip().lower() for cls in class_list]
    for alias in ("phishing", "malicious", "fraud", "bad"):
        if alias in normalized:
            index = normalized.index(alias)
            return float(probabilities[index])

    raise ValueError("Unable to determine phishing class index from model classes.")


def _categorize_risk(probability: float) -> str:
    """
    Map confidence percentage to risk category.
    
    WHY CATEGORIES?
    ===============
    Showing raw probabilities (0.7542) confuses users.
    Categories are intuitive:
    - "Safe" = Good to click
    - "Suspicious" = Be careful
    - "Likely Phishing" = Probably don't click
    - "High Risk Phishing" = Definitely phishing
    
    THRESHOLD STRATEGY:
    - <30%: Legit domains in training
    - 30-60%: ML uncertain (could go either way)
    - 60-85%: Likely phishing but not certain
    - ≥85%: High confidence phishing
    """
    percentage = probability * 100
    if percentage < 30:
        return "Safe"
    if percentage < 60:
        return "Suspicious"
    if percentage < 85:
        return "Likely Phishing"
    return "High Risk Phishing"


def predict_url(url: str) -> Tuple[int, float, str]:
    """
    Return the predicted label (0/1), phishing probability, and risk category using hybrid detection.
    
    MAIN PREDICTION FUNCTION
    ========================
    This orchestrates the entire prediction pipeline:
    
    INPUT: URL (string)
    PROCESS:
      1. Load trained model
      2. Extract 41 features
      3. Get ML model prediction
      4. Get semantic rule detection
      5. Combine both
      6. Categorize risk
    OUTPUT: (label, probability, risk_category)
    
    EXAMPLE USAGE:
    
    ```python
    label, prob, risk = predict_url("https://google.com")
    # label = 0 (legitimate)
    # prob = 0.15 (15% chance of phishing)
    # risk = "Safe"
    
    if label == 1:
        print(f"🚨 PHISHING! Confidence: {prob*100:.1f}%, Risk: {risk}")
    else:
        print(f"✓ Legitimate")
    ```
    
    WHY THIS PIPELINE?
    ==================
    Problem: Single approach (ML or rules) isn't enough
    Solution: Combine both complementary approaches
    
    ML Approach (RandomForest):
    ✓ Learns patterns from 247,950 historical URLs
    ✓ Captures complex feature combinations
    ✗ Misses obvious human signals (51% on obvious phishing)
    
    Semantic Rules:
    ✓ Catches human-obvious red flags (brand+keyword+TLD)
    ✗ Can't learn new patterns
    
    Hybrid (40% ML + 60% Semantic):
    ✓ Gets the best of both
    ✓ High confidence on both obvious (semantic) and subtle (ML) phishing
    """
    if not isinstance(url, str):
        raise TypeError("url must be a string")

    model, feature_columns = _load_artifacts()

    # ===== STEP 1: ML-BASED PREDICTION =====
    # Extract numeric features from URL
    features = extract_features_from_url(url)
    
    # Verify we have all expected features
    missing = [column for column in feature_columns if column not in features.columns]
    if missing:
        raise ValueError(f"Feature extractor missing columns: {missing}")

    # CRITICAL: Reindex to match training order
    # WHY: If features are in wrong order, predictions will be garbage
    features = features.reindex(columns=feature_columns, fill_value=0)

    # Get predictions from RandomForest
    proba = model.predict_proba(features)[0]          # Probabilities for each class
    label = int(model.predict(features)[0])           # Class (0 or 1)
    model_probability = _resolve_phishing_probability(proba, model.classes_)
    
    # ===== STEP 2: SEMANTIC-BASED DETECTION =====
    # Use rule-based detection on same URL
    semantic_indicators = detect_semantic_phishing(url)
    semantic_score = calculate_semantic_score(semantic_indicators)
    
    # ===== STEP 3: HYBRID COMBINATION =====
    # Blend ML (40%) + Semantic (60%) for final prediction
    combined_probability, confidence_level = hybrid_prediction(model_probability, semantic_score)
    
    # ===== STEP 4: DETERMINE FINAL LABEL =====
    # Convert probability to label (0/1)
    # WHY: Threshold at 0.5 (50%) is standard for binary classification
    # If probability ≥ 0.5, classify as phishing
    final_label = 1 if combined_probability >= 0.5 else 0
    
    # ===== STEP 5: CATEGORIZE RISK =====
    # Convert probability to human-readable category
    risk_category = _categorize_risk(combined_probability)

    return final_label, combined_probability, risk_category


def _cli() -> None:
    """
    Command-line interface for making predictions.
    
    WHY CLI?
    ========
    Sometimes users just want to quickly check a URL without opening the web app.
    The CLI lets us do:
    
    ```bash
    python predict.py "https://example.com"
    ```
    
    Output:
    ```json
    {
      "url": "https://example.com",
      "label": 0,
      "probability": 0.15,
      "risk_category": "Safe"
    }
    ```
    
    This is useful for:
    - Batch processing many URLs
    - Integration with other systems
    - Quick testing during development
    - Security researchers analyzing patterns
    """
    parser = argparse.ArgumentParser(description="Score a URL with the phishing detector.")
    parser.add_argument("url", help="URL to evaluate")
    args = parser.parse_args()

    label, phishing_prob, risk = predict_url(args.url)
    output: Dict[str, object] = {
        "url": args.url,
        "label": label,
        "probability": phishing_prob,
        "risk_category": risk,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    _cli()


__all__ = ["predict_url"]
