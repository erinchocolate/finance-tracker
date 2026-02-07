"""Category definitions and matching logic for transaction categorization."""

# Category keyword mappings
# Keywords are matched case-insensitively against Details and Particulars columns
CATEGORIES = {
    "Transport": ["bp"],
    "Groceries": ["countdown", "pak n save", "new world", "supermarket", "woolworths", "dairy", "four square"],
    "Insurance": ["insurance", "tower", "state", "aia", "southern cross", "nib", "rdi finance", "rdl premium finance"],
    "Investments": ["sharesies"],
    "Utilities": ["contact energy", "slingshot"],
    "Entertainment": ["globe", "youtube", "cinema",],
    "Dining": ["sushi", "cafe", "thai", "alexandre", "afghan darbar"],
    "Pet": ["dog", "vet", "pet", "animates", "petstock", "farmlands"],
    "Healthcare": ["pharmacy", "chemist", "doctor", "medical", "hospital", "dentist", "optometrist"],
    "Shopping": ["pb", "warehouse", "kmart", "target", "farmers", "briscoes", "mitre10", "mitre 10"],
    "Subscriptions": ["openai"],
    "Education": ["book"],
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

    # Joint account transfers are Income
    memo_lower = (particulars or "").lower()
    if "joint" in memo_lower or "joint accoun" in memo_lower:
        return "Income"

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
