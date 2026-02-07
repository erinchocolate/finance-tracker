"""Category definitions and matching logic for transaction categorization."""

# Category keyword mappings
# Keywords are matched case-insensitively against Details and Particulars columns
CATEGORIES = {
    "Transport": ["uber", "lime", "fuel", "z energy", "bp", "caltex", "mobil", "taxi", "at hop", "bus", "train"],
    "Groceries": ["countdown", "pak n save", "new world", "supermarket", "woolworths", "fresh choice", "four square"],
    "Insurance": ["insurance", "tower", "state", "aia", "southern cross", "nib", "rdi finance", "rdl premium finance"],
    "Investments": ["sharesies", "hatch", "investnow", "smartshares", "simplicity"],
    "Utilities": ["power", "electric", "water", "internet", "vodafone", "spark", "2degrees", "mercury", "genesis", "contact energy", "slingshot"],
    "Entertainment": ["netflix", "spotify", "disney", "apple music", "youtube", "cinema", "movie", "ticketmaster"],
    "Dining": ["restaurant", "cafe", "mcdonald", "uber eats", "menulog", "delivereasy", "burger", "pizza", "kfc", "wendy"],
    "Pet": ["dog", "vet", "pet", "animates", "petstock"],
    "Healthcare": ["pharmacy", "chemist", "doctor", "medical", "hospital", "dentist", "optometrist"],
    "Shopping": ["amazon", "warehouse", "kmart", "target", "farmers", "briscoes", "rebel sport"],
    "Subscriptions": ["subscription", "monthly", "annual fee", "membership"],
    "Education": ["school", "university", "course", "tuition", "book"],
    "Holiday": ["holiday"],
}


def categorize_transaction(details: str, particulars: str, transaction_type: str = "") -> str:
    """
    Categorize a transaction based on its details, particulars, and type.

    Args:
        details: The Details column value (merchant/payee name)
        particulars: The Particulars column value (additional details)
        transaction_type: The Type column value (e.g., Deposit, Payment)

    Returns:
        The category name, or "Other" if no match found
    """
    # Deposits are categorized as Income
    if transaction_type and transaction_type.lower() == "deposit":
        return "Income"

    # Loan Payments are categorized as Mortgage
    if transaction_type and transaction_type.lower() == "loan payment":
        return "Mortgage"

    # Combine and lowercase for matching
    search_text = f"{details or ''} {particulars or ''}".lower()

    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in search_text:
                return category

    return "Other"


def get_category_list() -> list:
    """Return a list of all available categories including 'Income' and 'Other'."""
    return list(CATEGORIES.keys()) + ["Income", "Mortgage", "Other"]
