"""Finance Tracker Dashboard - Streamlit Application."""

import io
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

from categories import categorize_transaction, get_category_list

# Google Sheets scope
GSHEET_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Page configuration
st.set_page_config(
    page_title="Finance Tracker Dashboard",
    page_icon="💰",
    layout="wide",
)

st.title("Finance Tracker Dashboard")
st.markdown("Upload your bank statements to analyze your expenses")


def load_xlsx(uploaded_file) -> pd.DataFrame:
    """Load xlsx file and normalize columns."""
    df = pd.read_excel(uploaded_file)

    # Ensure required columns exist
    required_columns = ["Transaction Date", "Details", "Amount"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(
            f"Missing required columns in {uploaded_file.name}: {missing}")
        return None

    # Normalize to standard columns
    df = df.rename(columns={
        "Transaction Date": "Date",
        "Details": "Description",
        "Particulars": "Memo",
        "Type": "Tran Type"
    })

    return df


def load_csv(uploaded_file) -> pd.DataFrame:
    """Load CSV file (with metadata header lines to skip) and normalize columns."""
    # Read CSV, skipping the metadata header lines (5 lines before column headers)
    df = pd.read_csv(uploaded_file, skiprows=5)
    # Remove any blank rows
    df = df.dropna(how='all')

    # Ensure required columns exist
    required_columns = ["Date", "Payee", "Amount"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(
            f"Missing required columns in {uploaded_file.name}: {missing}")
        return None

    # Normalize to standard columns
    df = df.rename(columns={
        "Payee": "Description",
        "Tran Type": "Tran Type"
    })

    return df


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process and categorize transaction data."""
    # Drop internal transfers (TFR IN / TFR OUT)
    if "Tran Type" in df.columns:
        df = df[~df["Tran Type"].isin(["TFR IN", "TFR OUT"])]

    # Convert Date to datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Add Month column for grouping
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    # Auto-categorize transactions
    df["Category"] = df.apply(
        lambda row: categorize_transaction(
            str(row.get("Description", "")),
            str(row.get("Memo", "")),
            str(row.get("Tran Type", ""))
        ),
        axis=1
    )

    # Add Expense/Income classification
    df["Type Classification"] = df["Amount"].apply(
        lambda x: "Income" if x > 0 else "Expense"
    )

    return df


def load_and_process_files(uploaded_files) -> pd.DataFrame:
    """Load multiple files and combine into single DataFrame."""
    all_dfs = []

    for uploaded_file in uploaded_files:
        if uploaded_file.name.endswith('.xlsx'):
            df = load_xlsx(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            df = load_csv(uploaded_file)
        else:
            st.warning(f"Unsupported file type: {uploaded_file.name}")
            continue

        if df is not None:
            df["Source"] = uploaded_file.name
            all_dfs.append(df)

    if not all_dfs:
        return None

    # Combine all dataframes
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Process the combined data
    return process_data(combined_df)


def display_summary_metrics(df: pd.DataFrame):
    """Display summary metrics at the top of the dashboard."""
    expenses_df = df[df["Amount"] < 0].copy()
    income_df = df[df["Amount"] > 0].copy()

    total_expenses = abs(expenses_df["Amount"].sum())
    total_income = income_df["Amount"].sum()
    num_months = df["Month"].nunique()
    avg_monthly = total_expenses / num_months if num_months > 0 else 0

    # Find top expense category
    if not expenses_df.empty:
        category_totals = expenses_df.groupby("Category")["Amount"].sum().abs()
        top_category = category_totals.idxmax()
        top_category_amount = category_totals.max()
    else:
        top_category = "N/A"
        top_category_amount = 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col2:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col3:
        st.metric("Avg Monthly Spend", f"${avg_monthly:,.2f}")
    with col4:
        st.metric("Top Category", f"{top_category}",
                  f"${top_category_amount:,.2f}")


def display_monthly_chart(df: pd.DataFrame):
    """Display monthly expenses bar chart."""
    expenses_df = df[df["Amount"] < 0].copy()
    expenses_df["Amount"] = expenses_df["Amount"].abs()

    monthly_expenses = expenses_df.groupby(
        "Month")["Amount"].sum().reset_index()
    # Sort chronologically by converting to datetime, then format as readable month
    monthly_expenses["Month_dt"] = pd.to_datetime(monthly_expenses["Month"])
    monthly_expenses = monthly_expenses.sort_values("Month_dt")
    monthly_expenses["Month_Label"] = monthly_expenses["Month_dt"].dt.strftime(
        "%b %Y")

    fig = px.bar(
        monthly_expenses,
        x="Month_Label",
        y="Amount",
        title="Monthly Expenses",
        labels={"Amount": "Total Spent ($)", "Month_Label": "Month"},
        color_discrete_sequence=["#FF6B6B"]
    )
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis={'type': 'category', 'categoryorder': 'array',
               'categoryarray': monthly_expenses["Month_Label"].tolist()}
    )

    st.plotly_chart(fig, use_container_width=True)


def display_category_chart(df: pd.DataFrame):
    """Display category breakdown pie chart."""
    expenses_df = df[df["Amount"] < 0].copy()
    expenses_df["Amount"] = expenses_df["Amount"].abs()

    category_totals = expenses_df.groupby(
        "Category")["Amount"].sum().reset_index()
    category_totals = category_totals.sort_values("Amount", ascending=False)

    fig = px.pie(
        category_totals,
        values="Amount",
        names="Category",
        title="Spending by Category",
        hole=0.4,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label+value",
        texttemplate="%{label}<br>$%{value:,.0f}<br>%{percent}"
    )

    st.plotly_chart(fig, use_container_width=True)


def display_category_bar_chart(df: pd.DataFrame):
    """Display category breakdown as horizontal bar chart."""
    expenses_df = df[df["Amount"] < 0].copy()
    expenses_df["Amount"] = expenses_df["Amount"].abs()

    category_totals = expenses_df.groupby(
        "Category")["Amount"].sum().reset_index()
    total = category_totals["Amount"].sum()
    category_totals["Percent"] = (
        category_totals["Amount"] / total * 100).round(1)
    category_totals["Label"] = category_totals.apply(
        lambda row: f"${row['Amount']:,.0f} ({row['Percent']}%)", axis=1
    )
    category_totals = category_totals.sort_values("Amount", ascending=True)

    fig = px.bar(
        category_totals,
        x="Amount",
        y="Category",
        orientation="h",
        title="Spending by Category",
        labels={"Amount": "Total Spent ($)", "Category": ""},
        color="Amount",
        color_continuous_scale="Reds",
        text="Label"
    )
    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)


def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    return output.getvalue()


# File uploader
uploaded_files = st.file_uploader(
    "Upload your bank statements",
    type=["xlsx", "csv"],
    accept_multiple_files=True,
    help="Drag and drop your bank statement files here (xlsx or csv)"
)

if uploaded_files:
    # Load and process data
    df = load_and_process_files(uploaded_files)

    if df is not None:
        st.success(f"Loaded {len(df)} transactions")

        # Editable transaction table (before charts so edits update visualizations)
        st.header("Transaction Details")
        st.markdown(
            "Edit categories or delete rows below. Changes will update the charts.")

        # Create editable dataframe
        category_options = get_category_list()

        # Select columns to display and edit
        display_columns = ["Date", "Description", "Memo",
                           "Amount", "Tran Type", "Category", "Source"]
        available_columns = [
            col for col in display_columns if col in df.columns]

        edited_df = st.data_editor(
            df[available_columns],
            column_config={
                "Category": st.column_config.SelectboxColumn(
                    "Category",
                    options=category_options,
                    required=True,
                ),
                "Amount": st.column_config.NumberColumn(
                    "Amount",
                    format="$%.2f",
                ),
                "Date": st.column_config.DateColumn(
                    "Date",
                    format="YYYY-MM-DD",
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="dynamic",
        )

        # Use edited dataframe for all visualizations
        df = edited_df.copy()
        df["Month"] = pd.to_datetime(
            df["Date"], errors="coerce").dt.to_period("M").astype(str)

        # Display summary metrics
        st.header("Summary")
        display_summary_metrics(df)

        # Charts section
        st.header("Visualizations")
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            display_monthly_chart(df)

        with chart_col2:
            display_category_chart(df)

        # Category bar chart (full width)
        display_category_bar_chart(df)

        # Download section
        st.header("Export Data")

        # Excel download
        excel_data = convert_df_to_excel(df)
        st.download_button(
            label="Download as Excel",
            data=excel_data,
            file_name="categorized_transactions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        # Google Sheets export
        st.subheader("Export to Google Sheets")

        # Check for local credentials file
        import os
        creds_path = os.path.join(
            os.path.dirname(__file__), "credentials.json")
        has_local_creds = os.path.exists(creds_path)

        if has_local_creds:
            st.success("Using saved credentials (credentials.json)")
            creds_file = None
        else:
            st.info(
                "Save your service account JSON as `credentials.json` in the app folder, or upload below:")
            creds_file = st.file_uploader(
                "Upload service account JSON key",
                type=["json"],
                help="Upload your Google Cloud service account credentials"
            )

        sheet_url = st.text_input(
            "Google Sheet URL",
            placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit"
        )

        can_export = sheet_url and (has_local_creds or creds_file)

        if st.button("Export to Google Sheets", disabled=not can_export):
            try:
                # Load credentials from local file or upload
                if has_local_creds:
                    with open(creds_path, "r") as f:
                        creds_data = json.load(f)
                else:
                    creds_data = json.load(creds_file)

                creds = Credentials.from_service_account_info(
                    creds_data, scopes=GSHEET_SCOPES)
                client = gspread.authorize(creds)

                # Open the spreadsheet
                spreadsheet = client.open_by_url(sheet_url)

                # Prepare summary data
                expenses_df = df[df["Amount"] < 0].copy()
                income_df = df[df["Amount"] > 0].copy()
                total_expenses = abs(expenses_df["Amount"].sum())
                total_income = income_df["Amount"].sum()

                # Prepare category breakdown (as dictionary for easy lookup)
                expenses_df["Amount"] = expenses_df["Amount"].abs()
                category_totals = expenses_df.groupby(
                    "Category")["Amount"].sum().to_dict()

                # Get the "finance" sheet
                try:
                    finance_sheet = spreadsheet.worksheet("Joint Finance")
                except gspread.exceptions.WorksheetNotFound:
                    st.error(
                        "Sheet named 'Joint Finance' not found. Please create it first.")
                    st.stop()

                # Read header row to find column positions
                headers = finance_sheet.row_values(1)

                # Build the row data based on headers
                row_data = []
                for header in headers:
                    header_lower = header.lower().strip()
                    if header_lower == "total expenses":
                        row_data.append(round(total_expenses, 2))
                    elif header_lower == "total income":
                        row_data.append(round(total_income, 2))
                    else:
                        # Match category name
                        matched = False
                        for cat_name, amount in category_totals.items():
                            if cat_name.lower() == header_lower:
                                row_data.append(round(amount, 2))
                                matched = True
                                break
                        if not matched:
                            row_data.append(0)  # No data for this category

                # Find next empty row
                all_values = finance_sheet.get_all_values()
                next_row = len(all_values) + 1

                # Write the data to the next row
                finance_sheet.update(f"A{next_row}", [row_data])

                st.success(
                    f"Exported to row {next_row} in 'Joint Finance' sheet!")

            except Exception as e:
                st.error(f"Error exporting to Google Sheets: {str(e)}")

        # Filter section
        st.header("Filter Transactions")
        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            selected_categories = st.multiselect(
                "Filter by Category",
                options=category_options,
                default=None,
            )

        with filter_col2:
            type_filter = st.selectbox(
                "Transaction Type",
                options=["All", "Expenses", "Income"],
            )

        with filter_col3:
            months = sorted(df["Month"].unique())
            selected_months = st.multiselect(
                "Filter by Month",
                options=months,
                default=None,
            )

        # Apply filters
        filtered_df = df.copy()

        if selected_categories:
            filtered_df = filtered_df[filtered_df["Category"].isin(
                selected_categories)]

        if type_filter == "Expenses":
            filtered_df = filtered_df[filtered_df["Amount"] < 0]
        elif type_filter == "Income":
            filtered_df = filtered_df[filtered_df["Amount"] > 0]

        if selected_months:
            filtered_df = filtered_df[filtered_df["Month"].isin(
                selected_months)]

        # Display filtered results
        st.dataframe(
            filtered_df[available_columns],
            hide_index=True,
            use_container_width=True,
        )

        st.caption(f"Showing {len(filtered_df)} of {len(df)} transactions")

else:
    st.info("Please upload one or more bank statement files to get started.")

    # Show expected format
    with st.expander("Supported file formats"):
        st.markdown("""
        **Excel (.xlsx) files** should contain:
        - **Transaction Date** - Date of the transaction
        - **Details** - Merchant/payee name (used for categorization)
        - **Particulars** - Additional details (optional)
        - **Amount** - Transaction amount (negative = expense, positive = income)
        - **Type** - Transaction type (Payment, Direct Debit, Deposit, etc.)

        **CSV files** should contain:
        - **Date** - Date of the transaction
        - **Payee** - Merchant/payee name (used for categorization)
        - **Memo** - Additional details (optional)
        - **Amount** - Transaction amount (negative = expense, positive = income)
        - **Tran Type** - Transaction type

        *Note: CSV files with 6 header lines (common bank export format) are supported.*
        """)
