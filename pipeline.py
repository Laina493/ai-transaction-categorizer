from typing import Dict, Any
from rules import rule_based_categorize
from classifier import classify_with_ml, is_confident

def categorize(description: str) -> Dict[str, Any]:
    # 1. Rules
    rule_category, rule_confidence = rule_based_categorize(description)
    if rule_category is not None:
        return {
            "category": rule_category,
            "source": "rule",
            "confidence": rule_confidence,
            "suggestion": None,
            "message": f"Categorised as '{rule_category}' by deterministic rules.",
        }

    # 2. ML Fallback
    ml_category, ml_confidence = classify_with_ml(description)
    if ml_category is not None and is_confident(ml_confidence):
        return {
            "category": ml_category,
            "source": "ml",
            "confidence": ml_confidence,
            "suggestion": None,
            "message": f"Categorised as '{ml_category}' by ML (confidence: {ml_confidence:.2%}).",
        }

    # 3. Human-in-the-loop
    if ml_category is None:
        suggestion_text = None
        confidence_value = 0.0
        message = "No rule matched and ML was unable to predict. Please specify the category."
    else:
        suggestion_text = ml_category
        confidence_value = ml_confidence
        message = f"No rule matched. ML suggests '{ml_category}' with low confidence ({ml_confidence:.2%}). Please confirm."

    return {
        "category": None,
        "source": "needs_review",
        "confidence": confidence_value,
        "suggestion": suggestion_text,
        "message": message,
    }

def generate_journal_entry(description: str, amount: float, category: str) -> dict:
    if not amount or amount <= 0:
        amount = 0.0
        
    if category in ["Expenses", "Assets", "Drawings"]:
        debit_account = category
        credit_account = "Bank" 
    elif category in ["Income", "Liabilities", "Equity"]:
        debit_account = "Bank"   
        credit_account = category
    else:
        debit_account = "Suspense / Uncategorised"
        credit_account = "Suspense / Uncategorised"

    return {
        "description": description,
        "amount": amount,
        "lines": [
            {"account": debit_account, "debit": amount, "credit": 0.0},
            {"account": credit_account, "debit": 0.0, "credit": amount}
        ]
    }