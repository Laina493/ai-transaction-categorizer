from transformers import pipeline

print("=" * 60)
print("Downloading zero-shot classification model...")
print("This is a ONE-TIME download of ~1.2 GB.")
print("Subsequent runs will use the cached version.")
print("=" * 60)

classifier = pipeline(
    "zero-shot-classification",
    model="valhalla/distilbart-mnli-12-1"
)

print("\nModel downloaded and loaded successfully!")

print("\nRunning a quick test...")
result = classifier(
    "Shell Fuel Windhoek",
    candidate_labels=["Expenses", "Income", "Assets", "Liabilities", "Equity", "Drawings"]
)

print("\nTest result:")
print(f"  Input: 'Shell Fuel Windhoek'")
print(f"  Predicted category: {result['labels'][0]}")
print(f"  Confidence: {result['scores'][0]:.2%}")
print(f"\n  All scores:")
for label, score in zip(result['labels'], result['scores']):
    print(f"    {label}: {score:.2%}")