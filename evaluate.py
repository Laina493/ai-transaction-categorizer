"""
Evaluation script: runs the full hybrid pipeline against sample_data.csv
and produces a comprehensive accuracy report.

Outputs:
    - Per-transaction classification table
    - Overall accuracy
    - Per-category accuracy breakdown
    - Source-layer breakdown (rule vs ML vs human-in-the-loop)
    - Confusion matrix
    - List of errors with justification
"""

import csv
from collections import Counter, defaultdict
from pipeline import categorize


def load_data(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluate(data_path: str = "sample_data.csv") -> None:
    rows = load_data(data_path)

    total = 0
    correct = 0
    errors = []

    # Track statistics
    per_category_total = Counter()
    per_category_correct = Counter()
    source_counts = Counter()

    # Confusion matrix: expected -> Counter(predicted)
    confusion = defaultdict(Counter)

    print("=" * 105)
    print(f"{'Date':<12} {'Description':<45} {'Expected':<13} {'Predicted':<13} {'Source':<13} {'OK'}")
    print("=" * 105)

    for row in rows:
        desc = row["description"]
        expected = row["expected_category"]
        result = categorize(desc)
        predicted = result["category"]
        source = result["source"]

        total += 1
        per_category_total[expected] += 1
        source_counts[source] += 1

        match = (predicted == expected) if predicted else False
        if match:
            correct += 1
            per_category_correct[expected] += 1

        confusion[expected][predicted or "(unresolved)"] += 1

        ok_symbol = "OK" if match else "ERR"
        short_desc = desc[:42] + "..." if len(desc) > 45 else desc
        predicted_disp = predicted if predicted else "(needs review)"

        print(f"{row['date']:<12} {short_desc:<45} {expected:<13} {predicted_disp:<13} {source:<13} {ok_symbol}")

        if not match:
            errors.append({
                "date": row["date"],
                "description": desc,
                "expected": expected,
                "predicted": predicted,
                "source": source,
                "confidence": result["confidence"],
                "message": result["message"],
            })

    # ---- Report -------------------------------------------------------------
    print("=" * 105)

    print("\n┌─ OVERALL METRICS ──────────────────────────────────────────────")
    print(f"│  Total transactions     : {total}")
    print(f"│  Correctly categorised  : {correct}")
    print(f"│  Overall accuracy       : {correct / total * 100:.2f}%")
    print(f"│  Errors                 : {total - correct}")
    print(f"└────────────────────────────────────────────────────────────────")

    print("\n┌─ SOURCE LAYER BREAKDOWN ──────────────────────────────────────")
    for source, count in source_counts.most_common():
        pct = count / total * 100
        print(f"│  {source:<20}: {count:>3} ({pct:>5.2f}%)")
    print(f"└────────────────────────────────────────────────────────────────")

    print("\n┌─ PER-CATEGORY ACCURACY ───────────────────────────────────────")
    print(f"│  {'Category':<15} {'Correct':<10} {'Total':<10} {'Accuracy'}")
    print(f"│  {'-' * 55}")
    for category in sorted(per_category_total.keys()):
        correct_count = per_category_correct[category]
        total_count = per_category_total[category]
        acc = correct_count / total_count * 100 if total_count else 0
        print(f"│  {category:<15} {correct_count:<10} {total_count:<10} {acc:.2f}%")
    print(f"└────────────────────────────────────────────────────────────────")

    print("\n┌─ CONFUSION MATRIX (Expected → Predicted) ─────────────────────")
    for expected in sorted(confusion.keys()):
        print(f"│  {expected}:")
        for predicted, count in confusion[expected].most_common():
            marker = "✓" if predicted == expected else "✗"
            print(f"│      {marker}  {predicted:<20}: {count}")
    print(f"└────────────────────────────────────────────────────────────────")

    if errors:
        print("\n┌─ ERROR ANALYSIS ──────────────────────────────────────────────")
        for i, err in enumerate(errors, 1):
            print(f"│")
            print(f"│  Error #{i}")
            print(f"│    Date        : {err['date']}")
            print(f"│    Description : {err['description']}")
            print(f"│    Expected    : {err['expected']}")
            print(f"│    Predicted   : {err['predicted'] or '(needs review)'}")
            print(f"│    Source      : {err['source']}")
            print(f"│    Confidence  : {err['confidence']:.4f}")
            print(f"│    Message     : {err['message']}")
        print(f"└────────────────────────────────────────────────────────────────")

    print("\n✓ Evaluation complete.\n")


if __name__ == "__main__":
    evaluate()