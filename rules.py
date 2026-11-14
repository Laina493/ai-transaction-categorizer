import re

KEYWORD_RULES = [
    # Income
    ("capitalised interest credit", "Income"),
    ("interest credit", "Income"),
    ("cash dep", "Income"),
    ("deposit", "Income"),
    ("salary", "Income"),
    ("wages", "Income"),
    ("business", "Income"),
    ("work", "Income"),
    ("innocent", "Income"),
    ("von baums", "Income"),
    ("annacletta", "Income"),
    ("microbus", "Income"),
    ("alec", "Income"),

    # Liabilities
    ("loan repayment", "Liabilities"),
    ("loan to company", "Liabilities"),
    ("loan to business", "Liabilities"),
    ("loan", "Liabilities"),

    # Drawings
    ("cash withdrawal", "Drawings"),
    ("atm withdrawal", "Drawings"),
    ("tinashe", "Drawings"),
    ("anna's air ticket", "Drawings"),
    ("huku dr tagarira", "Drawings"),
    ("dr tagarira", "Drawings"),
    ("maid", "Drawings"),
    ("gas", "Drawings"),

    # Assets
    ("a j auto parts", "Assets"),
    ("masterparts", "Assets"),
    ("auto speed", "Assets"),
    ("hyundai", "Assets"),
    ("tyre rack", "Assets"),

    # Expenses (Bank fees)
    ("withholding tax", "Expenses"),
    ("duty on debit", "Expenses"),
    ("atm withdrawal fees", "Expenses"),
    ("card fee", "Expenses"),
    ("card protection", "Expenses"),
    ("bank confirmation", "Expenses"),
    ("internet banking", "Expenses"),
    ("easy wallet", "Expenses"),
    ("beneficiary payment", "Expenses"),
    ("mbapp", "Expenses"),
    ("rev stamp", "Expenses"),
    ("2018 interest", "Expenses"),
    ("tax interest", "Expenses"),

    # Expenses (Taxes)
    ("income tax", "Expenses"),
    ("tax 20", "Expenses"),
    ("tax", "Expenses"),

    # Expenses (Bills)
    ("rental", "Expenses"),
    ("electricity prepaid", "Expenses"),
    ("electricityprepaid", "Expenses"),
    ("prepaid", "Expenses"),
    ("insurance", "Expenses"),
    ("medical", "Expenses"),
    ("natis", "Expenses"),
    ("shell", "Expenses"),

    # Expenses (Fallback)
    ("goods and service", "Expenses"),
    ("goods with cashb", "Expenses"),
    ("fees", "Expenses"),
]

MCC_RULES = {
    # Retail
    "5411": "Expenses",
    "5422": "Expenses",
    "5499": "Expenses",
    "5812": "Expenses",
    "5813": "Expenses",
    "5814": "Expenses",
    "5921": "Expenses",
    # Fuel & Auto
    "5541": "Expenses",
    "5542": "Expenses",
    "5533": "Assets",
    "7538": "Expenses",
    # Clothing/Retail
    "5651": "Expenses",
    "5691": "Expenses",
    "5732": "Assets",
    "5311": "Expenses",
    "5399": "Expenses",
    "5251": "Assets",
    # Health
    "5912": "Expenses",
    "8099": "Expenses",
    # Gov/Services
    "9399": "Expenses",
    "6211": "Expenses",
    "7011": "Expenses",
    "0763": "Expenses",
    "4812": "Expenses",
}

_MCC_PATTERN = re.compile(r"\b(\d{4})\b")

def rule_based_categorize(description: str) -> tuple:
    if not description:
        return (None, 0.0)

    desc_lower = description.lower()

    for keyword, category in KEYWORD_RULES:
        if keyword in desc_lower:
            return (category, 1.0)

    mcc_matches = _MCC_PATTERN.findall(description)
    for mcc in mcc_matches:
        if mcc in MCC_RULES:
            return (MCC_RULES[mcc], 0.9)

    return (None, 0.0)