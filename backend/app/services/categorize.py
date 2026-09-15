"""Deterministic, keyword-based transaction categorization.

Starts from merchant/description substrings mapped to a (parent, child)
category pair. This is intentionally simple and auditable — a later pass
can layer an LLM or embedding-based classifier on top for the merchants
these rules miss, without changing the category schema underneath it.
"""
from decimal import Decimal

# Ordered most-specific-first: the first matching keyword wins.
KEYWORD_RULES: list[tuple[str, str, str]] = [
    # Food & Dining
    ("swiggy", "Food & Dining", "Delivery"),
    ("zomato", "Food & Dining", "Delivery"),
    ("dominos", "Food & Dining", "Restaurants"),
    ("mcdonald", "Food & Dining", "Restaurants"),
    ("starbucks", "Food & Dining", "Restaurants"),
    ("cafe", "Food & Dining", "Restaurants"),
    ("restaurant", "Food & Dining", "Restaurants"),
    ("bigbasket", "Food & Dining", "Groceries"),
    ("blinkit", "Food & Dining", "Groceries"),
    ("zepto", "Food & Dining", "Groceries"),
    ("dmart", "Food & Dining", "Groceries"),
    ("grocery", "Food & Dining", "Groceries"),
    # Transport
    ("uber", "Transport", "Ride-hailing"),
    ("ola", "Transport", "Ride-hailing"),
    ("rapido", "Transport", "Ride-hailing"),
    ("indian oil", "Transport", "Fuel"),
    ("bharat petroleum", "Transport", "Fuel"),
    ("hp petrol", "Transport", "Fuel"),
    ("petrol", "Transport", "Fuel"),
    ("fuel", "Transport", "Fuel"),
    ("irctc", "Transport", "Public Transit"),
    ("metro", "Transport", "Public Transit"),
    ("parking", "Transport", "Parking"),
    # Shopping
    ("amazon", "Shopping", "Online Shopping"),
    ("flipkart", "Shopping", "Online Shopping"),
    ("myntra", "Shopping", "Clothing"),
    ("ajio", "Shopping", "Clothing"),
    ("croma", "Shopping", "Electronics"),
    ("reliance digital", "Shopping", "Electronics"),
    ("ikea", "Shopping", "Home & Furniture"),
    # Bills & Utilities
    ("electricity", "Bills & Utilities", "Electricity"),
    ("bescom", "Bills & Utilities", "Electricity"),
    ("airtel", "Bills & Utilities", "Mobile Recharge"),
    ("jio", "Bills & Utilities", "Mobile Recharge"),
    ("vodafone", "Bills & Utilities", "Mobile Recharge"),
    ("vi recharge", "Bills & Utilities", "Mobile Recharge"),
    ("broadband", "Bills & Utilities", "Internet"),
    ("wifi", "Bills & Utilities", "Internet"),
    ("act fibernet", "Bills & Utilities", "Internet"),
    ("rent", "Bills & Utilities", "Rent"),
    ("water bill", "Bills & Utilities", "Water & Gas"),
    ("gas bill", "Bills & Utilities", "Water & Gas"),
    # Entertainment
    ("netflix", "Entertainment", "Streaming"),
    ("spotify", "Entertainment", "Streaming"),
    ("prime video", "Entertainment", "Streaming"),
    ("hotstar", "Entertainment", "Streaming"),
    ("youtube premium", "Entertainment", "Streaming"),
    ("pvr", "Entertainment", "Movies"),
    ("inox", "Entertainment", "Movies"),
    ("bookmyshow", "Entertainment", "Movies"),
    ("steam", "Entertainment", "Gaming"),
    ("playstation", "Entertainment", "Gaming"),
    # Health
    ("pharmacy", "Health", "Pharmacy"),
    ("apollo", "Health", "Pharmacy"),
    ("medplus", "Health", "Pharmacy"),
    ("hospital", "Health", "Medical"),
    ("clinic", "Health", "Medical"),
    ("cult.fit", "Health", "Fitness"),
    ("gym", "Health", "Fitness"),
    # Financial
    ("emi", "Financial", "EMI & Loans"),
    ("loan", "Financial", "EMI & Loans"),
    ("insurance", "Financial", "Insurance"),
    ("mutual fund", "Financial", "Investments"),
    ("zerodha", "Financial", "Investments"),
    ("groww", "Financial", "Investments"),
    ("sip", "Financial", "Investments"),
    ("annual fee", "Financial", "Fees & Charges"),
    ("late fee", "Financial", "Fees & Charges"),
    ("penalty", "Financial", "Fees & Charges"),
    # Income
    ("salary", "Income", "Salary"),
    ("interest credit", "Income", "Interest"),
    ("refund", "Income", "Refunds"),
    ("reversal", "Income", "Refunds"),
]


def suggest_category(merchant: str, raw_description: str, amount: Decimal) -> tuple[str, str, float] | None:
    """Returns (parent_name, child_name, confidence) or None if nothing matched."""
    haystack = f"{merchant} {raw_description}".lower()

    for keyword, parent, child in KEYWORD_RULES:
        if keyword in haystack:
            return parent, child, 0.85

    # Large, unlabeled credits are very often salary.
    if amount > 0 and amount >= Decimal("20000"):
        return "Income", "Salary", 0.4

    return None
