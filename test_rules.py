"""
Test runner: applies the rule engine to sample_data.csv and reports accuracy.
"""

import csv
from collections import Counter
from rules import rule_based_categorize


def load_data(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = load_data("sample_data.csv")

    correct = 0
    total = 0
    unmatched = []
    mismatches = []
    per_category = Counter()

    print("=" * 100)
    print(f"{'Date':<12} {'Description':<55} {'Expected':<13} {'Predicted':<13} {'Match':<6}")
    print("=" * 100)

    for row in rows:
        desc = row["description"]
        expected = row["expected_category"]

        predicted, confidence = rule_based_categorize(desc)
        predicted_display = predicted if predicted else "UNMATCHED"
        match = "YES" if predicted == expected else "NO"

        total += 1
        if match == "YES":
            correct += 1
            per_category[expected] += 1
        else:
            if predicted is None:
                unmatched.append(row)
            else:
                mismatches.append((row, predicted, confidence))

        short_desc = desc[:52] + "..." if len(desc) > 55 else desc
        print(f"{row['date']:<12} {short_desc:<55} {expected:<13} {predicted_display:<13} {match:<6}")

    print("=" * 100)
    print(f"\nRESULTS")
    print(f"  Total transactions  : {total}")
    print(f"  Correctly categorised: {correct}")
    print(f"  Accuracy            : {correct / total * 100:.2f}%")
    print(f"  Unmatched           : {len(unmatched)}")
    print(f"  Misclassified       : {len(mismatches)}")

    if unmatched:
        print(f"\n  UNMATCHED TRANSACTIONS (no rule fired):")
        for row in unmatched:
            print(f"    - [{row['date']}] {row['description'][:80]}")

    if mismatches:
        print(f"\n  MISCLASSIFIED TRANSACTIONS (rule fired but wrong):")
        for row, predicted, conf in mismatches:
            print(f"    - [{row['date']}] {row['description'][:70]}")
            print(f"        Expected: {row['expected_category']}  |  Predicted: {predicted} ({conf:.2f})")

    print(f"\n  Per-category correct counts:")
    for cat, count in sorted(per_category.items()):
        print(f"    {cat:<15}: {count}")


if __name__ == "__main__":
    main()