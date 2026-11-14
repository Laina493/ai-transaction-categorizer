"""
Zero-shot ML classifier wrapper for the transaction categorisation system.

Wraps the valhalla/distilbart-mnli-12-1 Hugging Face model and exposes
a single function `classify_with_ml()` that takes a transaction
description and returns a (category, confidence) tuple.

The model is loaded once and cached for the lifetime of the process.

Model: https://huggingface.co/valhalla/distilbart-mnli-12-1
Task:  Zero-shot classification
"""

from transformers import pipeline
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL_NAME = "valhalla/distilbart-mnli-12-1"

# The six core financial statement elements from the research proposal
CANDIDATE_LABELS = [
    "Assets",
    "Liabilities",
    "Equity",
    "Income",
    "Expenses",
    "Drawings",
]

# Minimum confidence for the ML prediction to be accepted without
# falling back to human-in-the-loop prompt.
ACCEPTANCE_THRESHOLD = 0.60


# ---------------------------------------------------------------------------
# Model loading (lazy + cached)
# ---------------------------------------------------------------------------

_classifier = None  # module-level cache


def _load_classifier():
    """Load the zero-shot classifier once and cache it for the process."""
    global _classifier
    if _classifier is None:
        print(f"[classifier] Loading model: {MODEL_NAME} ...")
        _classifier = pipeline(
            "zero-shot-classification",
            model=MODEL_NAME,
        )
        print("[classifier] Model loaded successfully.")
    return _classifier


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_with_ml(description: str) -> Tuple[Optional[str], float]:
    """
    Classify a transaction description using the zero-shot ML model.

    Args:
        description: The transaction description text.

    Returns:
        (category, confidence) tuple where:
            - category is the top predicted label (or None if description empty)
            - confidence is the probability score for that label [0.0, 1.0]
    """
    if not description or not description.strip():
        return (None, 0.0)

    classifier = _load_classifier()

    result = classifier(description, candidate_labels=CANDIDATE_LABELS)

    top_label = result["labels"][0]
    top_score = float(result["scores"][0])

    return (top_label, top_score)


def is_confident(confidence: float) -> bool:
    """
    Return True if the ML prediction is confident enough to accept
    without human-in-the-loop clarification.
    """
    return confidence >= ACCEPTANCE_THRESHOLD


# ---------------------------------------------------------------------------
# Self-test when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("Testing classifier.py on difficult transactions")
    print("=" * 70)

    test_cases = [
        # Cases from sample_data.csv that the rule engine couldn't handle
        "CREDIT",
        "GOODS AND SERVICE (*4023 - 02/12/2020) 5533 A J AUTO PARTS WINDHOEK NA",
        # Sanity-check cases
        "Shell Fuel Windhoek",
        "CASH WITHDRAWAL (*4023 - 08/03/2020) 6011 ATM202 OMARURU",
        "CAPITALISED INTEREST CREDIT",
        "LOAN REPAYMENT DR TAGARIRA",
    ]

    print(f"\n{'Description':<70} {'Predicted':<14} {'Confidence':<12} {'Accept?':<8}")
    print("-" * 110)

    for desc in test_cases:
        category, confidence = classify_with_ml(desc)
        accept = "YES" if is_confident(confidence) else "NO (prompt user)"
        short_desc = desc[:67] + "..." if len(desc) > 70 else desc
        print(f"{short_desc:<70} {str(category):<14} {confidence:<12.4f} {accept:<8}")

    print("\nDone.")