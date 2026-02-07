# Finance Tracker Dashboard

A Streamlit app for analyzing bank statements with auto-categorization and interactive visualizations.

## Features

- **Multi-file Upload**: Drag and drop multiple bank statements (xlsx and csv formats)
- **Auto-Categorization**: Automatically categorizes transactions based on keywords
- **Interactive Charts**: Monthly expenses bar chart and category breakdown pie chart
- **Editable Transactions**: Manually adjust categories or delete rows
- **Google Sheets Export**: Export summary and category breakdown to your Google Sheet
- **Filtering**: Filter transactions by category, type, or month

## Quick Start

```bash
# Clone the repository
git clone https://github.com/erinchocolate/finance-tracker.git
cd finance-tracker

# Install dependencies
./setup.sh

# Run the app
./run.sh
```

Then open http://localhost:8501 in your browser.

## Supported File Formats

### Excel (.xlsx)
Expected columns:
- `Transaction Date` - Date of the transaction
- `Details` - Merchant/payee name
- `Particulars` - Additional details (optional)
- `Amount` - Transaction amount (negative = expense, positive = income)
- `Type` - Transaction type (Payment, Direct Debit, Deposit, etc.)

### CSV
Expected columns:
- `Date` - Date of the transaction
- `Payee` - Merchant/payee name
- `Memo` - Additional details (optional)
- `Amount` - Transaction amount
- `Tran Type` - Transaction type

Note: CSV files with 5 metadata header lines (common bank export format) are supported.

## Auto-Categorization Rules

Transactions are automatically categorized based on keywords:

| Category | Keywords |
|----------|----------|
| Groceries | countdown, pak n save, new world, woolworths, dairy |
| Transport | uber, lime, fuel, z energy, bp, caltex |
| Dining | sushi, cafe, thai, uber eats, burger, pizza |
| Utilities | power, electric, water, internet, vodafone, spark, slingshot |
| Entertainment | globe, spotify, disney, apple music, youtube |
| Shopping | pb, warehouse, kmart, farmers, briscoes, mitre10 |
| Insurance | insurance, tower, state, rdi finance, rdl premium finance |
| Healthcare | pharmacy, chemist, doctor, medical, hospital |
| Pet | dog, vet, pet, animates, farmlands |
| Investments | sharesies, hatch, investnow |
| Subscriptions | subscription, monthly, annual fee, openai |
| Education | school, university, course, tuition |
| Holiday | holiday |

Special rules:
- `Deposit` type → Income
- `Loan Payment` type → Mortgage
- `TFR IN` / `TFR OUT` types → Excluded (internal transfers)
- Memo contains "joint" → Income

## Google Sheets Export

### Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project and enable:
   - Google Sheets API
   - Google Drive API
3. Create a Service Account and download the JSON key
4. Save the JSON key as `credentials.json` in the app folder
5. Share your Google Sheet with the service account email (found in the JSON file)

### Sheet Format

Create a sheet named "Joint Finance" with headers in row 1:

```
| Total Expenses | Total Income | Mortgage | Investments | Insurance | Utilities | Groceries | Dining | Holiday | Pet | Transport | Entertainment | Shopping | Healthcare | ...
```

The app will match your category columns and write values to the next available row.

## Project Structure

```
finance-tracker/
├── app.py              # Main Streamlit application
├── categories.py       # Category definitions and matching logic
├── requirements.txt    # Python dependencies
├── credentials.json    # Google service account key (not in repo)
├── setup.sh           # First-time setup script
├── run.sh             # Run the app locally
└── README.md
```

## Dependencies

- streamlit
- pandas
- openpyxl
- plotly
- gspread
- google-auth

## License

MIT
