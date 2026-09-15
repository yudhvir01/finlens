# The default category tree seeded once as system categories (user_id=None).
# Every account's transactions get categorized against this tree unless the
# user creates their own categories later.

SEED_CATEGORIES: dict[str, list[str]] = {
    "Income": ["Salary", "Refunds", "Interest", "Other Income"],
    "Food & Dining": ["Restaurants", "Delivery", "Groceries"],
    "Transport": ["Fuel", "Ride-hailing", "Public Transit", "Parking"],
    "Shopping": ["Online Shopping", "Electronics", "Clothing", "Home & Furniture"],
    "Bills & Utilities": ["Electricity", "Internet", "Mobile Recharge", "Rent", "Water & Gas"],
    "Entertainment": ["Streaming", "Movies", "Gaming"],
    "Health": ["Pharmacy", "Medical", "Fitness"],
    "Transfers": ["Self Transfer", "Sent to Others"],
    "Financial": ["EMI & Loans", "Insurance", "Investments", "Fees & Charges"],
    "Other": ["Uncategorized"],
}
