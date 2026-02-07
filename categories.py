"""Category definitions and matching logic for transaction categorization."""

# Category keyword mappings
# Keywords are matched case-insensitively against Details and Particulars columns
CATEGORIES = {
    "Transport": ["uber", "lime", "fuel", "z energy", "bp", "caltex", "mobil", "taxi", "at hop", "bus", "train"],
    "Groceries": ["countdown", "pak n save", "new world", "supermarket", "woolworths", "fresh choice", "four square"],
    "Insurance": ["insurance", "tower", "state", "aia", "southern cross", "nib"],
    "Investments": ["sharesies", "hatch", "investnow", "smartshares", "simplicity"],
    "Utilities": ["power", "electric", "water", "internet", "vodafone", "spark", "2degrees", "mercury", "genesis", "contact energy"],
    "Entertainment": ["netflix", "spotify", "disney", "apple music", "youtube", "cinema", "movie", "ticketmaster"],
    "Dining": ["restaurant", "cafe", "mcdonald", "uber eats", "menulog", "delivereasy", "burger", "pizza", "kfc", "wendy"],
    "Pet": ["dog", "vet", "pet", "animates", "petstock"],
    "Healthcare": ["pharmacy", "chemist", "doctor", "medical", "hospital", "dentist", "optometrist"],
    "Shopping": ["amazon", "warehouse", "kmart", "target", "farmers", "briscoes", "rebel sport"],
    "Subscriptions": ["subscription", "monthly", "annual fee", "membership"],
    "Transfer": ["transfer", "payment to", "payment from"],
    "ATM": ["atm", "cash", "withdrawal"],
    "Rent/Mortgage": ["rent", "mortgage", "housing", "landlord", "property"],
    "Education": ["school", "university", "course", "tuition", "book"],
}


def categorize_transaction(details: str, particulars: str) -> str:
    """
    Categorize a transaction based on its details and particulars.

    Args:
        details: The Details column value (merchant/payee name)
        particulars: The Particulars column value (additional details)

    Returns:
        The category name, or "Other" if no match found
    """
    # Combine and lowercase for matching
    search_text = f"{details or ''} {particulars or ''}".lower()

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in search_text:
                return category

    return "Other"


def get_category_list() -> list:
    """Return a list of all available categories including 'Other'."""
    return list(CATEGORIES.keys()) + ["Other"]
