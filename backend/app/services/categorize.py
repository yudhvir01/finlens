"""Deterministic, keyword-based transaction categorization.

Starts from merchant/description substrings mapped to a (parent, child)
category pair. This is intentionally simple and auditable — a later pass
can layer an LLM or embedding-based classifier on top for the merchants
these rules miss, without changing the category schema underneath it.
"""
from decimal import Decimal

# Ordered most-specific-first: the first matching keyword wins.
# The 4th element restricts a keyword to the cleaned merchant name only,
# instead of the full raw description — needed for brand names that also
# show up as a UPI payment-service-provider/routing bank on transactions
# for a completely different merchant (e.g. "AIRTEL PAYMENTS BANK" routing
# a payment to some unrelated company would otherwise false-match "airtel").
KEYWORD_RULES: list[tuple[str, str, str, bool]] = [
    # Food & Dining
    ("swiggy", "Food & Dining", "Delivery", False),
    ("zomato", "Food & Dining", "Delivery", False),
    ("dominos", "Food & Dining", "Restaurants", False),
    ("mcdonald", "Food & Dining", "Restaurants", False),
    ("starbucks", "Food & Dining", "Restaurants", False),
    ("cafe", "Food & Dining", "Restaurants", False),
    ("restaurant", "Food & Dining", "Restaurants", False),
    ("bigbasket", "Food & Dining", "Groceries", False),
    ("blinkit", "Food & Dining", "Groceries", False),
    ("zepto", "Food & Dining", "Groceries", False),
    ("dmart", "Food & Dining", "Groceries", False),
    ("grocery", "Food & Dining", "Groceries", False),
    # Transport
    ("uber", "Transport", "Ride-hailing", False),
    ("ola", "Transport", "Ride-hailing", False),
    ("rapido", "Transport", "Ride-hailing", False),
    ("indian oil", "Transport", "Fuel", False),
    ("bharat petroleum", "Transport", "Fuel", False),
    ("hp petrol", "Transport", "Fuel", False),
    ("petrol", "Transport", "Fuel", False),
    ("fuel", "Transport", "Fuel", False),
    ("irctc", "Transport", "Public Transit", False),
    ("metro", "Transport", "Public Transit", False),
    ("parking", "Transport", "Parking", False),
    # Shopping
    ("amazon", "Shopping", "Online Shopping", False),
    ("flipkart", "Shopping", "Online Shopping", False),
    ("myntra", "Shopping", "Clothing", False),
    ("ajio", "Shopping", "Clothing", False),
    ("croma", "Shopping", "Electronics", False),
    ("reliance digital", "Shopping", "Electronics", False),
    ("ikea", "Shopping", "Home & Furniture", False),
    # Bills & Utilities
    ("electricity", "Bills & Utilities", "Electricity", False),
    ("bescom", "Bills & Utilities", "Electricity", False),
    ("airtel", "Bills & Utilities", "Mobile Recharge", True),
    ("jio", "Bills & Utilities", "Mobile Recharge", True),
    ("vodafone", "Bills & Utilities", "Mobile Recharge", True),
    ("vi recharge", "Bills & Utilities", "Mobile Recharge", True),
    ("broadband", "Bills & Utilities", "Internet", False),
    ("wifi", "Bills & Utilities", "Internet", False),
    ("act fibernet", "Bills & Utilities", "Internet", False),
    ("rent", "Bills & Utilities", "Rent", False),
    ("water bill", "Bills & Utilities", "Water & Gas", False),
    ("gas bill", "Bills & Utilities", "Water & Gas", False),
    # Entertainment
    ("netflix", "Entertainment", "Streaming", False),
    ("spotify", "Entertainment", "Streaming", False),
    ("prime video", "Entertainment", "Streaming", False),
    ("hotstar", "Entertainment", "Streaming", False),
    ("youtube premium", "Entertainment", "Streaming", False),
    ("pvr", "Entertainment", "Movies", False),
    ("inox", "Entertainment", "Movies", False),
    ("bookmyshow", "Entertainment", "Movies", False),
    ("steam", "Entertainment", "Gaming", False),
    ("playstation", "Entertainment", "Gaming", False),
    # Health
    ("pharmacy", "Health", "Pharmacy", False),
    ("apollo", "Health", "Pharmacy", False),
    ("medplus", "Health", "Pharmacy", False),
    ("hospital", "Health", "Medical", False),
    ("clinic", "Health", "Medical", False),
    ("healthcare", "Health", "Medical", False),
    ("cult.fit", "Health", "Fitness", False),
    ("gym", "Health", "Fitness", False),
    # Financial
    ("emi", "Financial", "EMI & Loans", False),
    ("loan", "Financial", "EMI & Loans", False),
    ("insurance", "Financial", "Insurance", False),
    ("mutual fund", "Financial", "Investments", False),
    ("zerodha", "Financial", "Investments", False),
    ("groww", "Financial", "Investments", False),
    ("sip", "Financial", "Investments", False),
    ("annual fee", "Financial", "Fees & Charges", False),
    ("late fee", "Financial", "Fees & Charges", False),
    ("penalty", "Financial", "Fees & Charges", False),
    ("bounce chrgs", "Financial", "Fees & Charges", False),
    # Income
    ("salary", "Income", "Salary", False),
    ("interest credit", "Income", "Interest", False),
    ("refund", "Income", "Refunds", False),
    ("reversal", "Income", "Refunds", False),
]


def suggest_category(merchant: str, raw_description: str, amount: Decimal) -> tuple[str, str, float] | None:
    """Returns (parent_name, child_name, confidence) or None if nothing matched."""
    merchant_haystack = merchant.lower()
    full_haystack = f"{merchant} {raw_description}".lower()

    for keyword, parent, child, merchant_only in KEYWORD_RULES:
        haystack = merchant_haystack if merchant_only else full_haystack
        if keyword in haystack:
            return parent, child, 0.85

    # Large, unlabeled credits are very often salary.
    if amount > 0 and amount >= Decimal("20000"):
        return "Income", "Salary", 0.4

    return None
