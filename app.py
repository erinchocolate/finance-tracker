"""Finance Tracker Dashboard - Streamlit Application."""

import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from categories import categorize_transaction, get_category_list

# Page configuration
st.set_page_config(
    page_title="Finance Tracker Dashboard",
    page_icon="💰",
    layout="wide",
)

st.title("Finance Tracker Dashboard")
st.markdown("Upload your bank statement to analyze your expenses")


def load_and_process_data(uploaded_file) -> pd.DataFrame:
    """Load xlsx file and process transactions."""
    df = pd.read_excel(uploaded_file)

    # Ensure required columns exist
    required_columns = ["Transaction Date", "Details", "Amount"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        return None

    # Convert Transaction Date to datetime
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"], errors="coerce")

    # Add Month column for grouping
    df["Month"] = df["Transaction Date"].dt.to_period("M").astype(str)

    # Auto-categorize transactions
    df["Category"] = df.apply(
        lambda row: categorize_transaction(
            str(row.get("Details", "")),
            str(row.get("Particulars", ""))
        ),
        axis=1
    )

    # Add Expense/Income classification
    df["Type Classification"] = df["Amount"].apply(
        lambda x: "Income" if x > 0 else "Expense"
    )

    return df


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
        st.metric("Top Category", f"{top_category}", f"${top_category_amount:,.2f}")


def display_monthly_chart(df: pd.DataFrame):
    """Display monthly expenses bar chart."""
    expenses_df = df[df["Amount"] < 0].copy()
    expenses_df["Amount"] = expenses_df["Amount"].abs()

    monthly_expenses = expenses_df.groupby("Month")["Amount"].sum().reset_index()
    monthly_expenses = monthly_expenses.sort_values("Month")

    fig = px.bar(
        monthly_expenses,
        x="Month",
        y="Amount",
        title="Monthly Expenses",
        labels={"Amount": "Total Spent ($)", "Month": "Month"},
        color_discrete_sequence=["#FF6B6B"]
    )
    fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width=True)


def display_category_chart(df: pd.DataFrame):
    """Display category breakdown pie chart."""
    expenses_df = df[df["Amount"] < 0].copy()
    expenses_df["Amount"] = expenses_df["Amount"].abs()

    category_totals = expenses_df.groupby("Category")["Amount"].sum().reset_index()
    category_totals = category_totals.sort_values("Amount", ascending=False)

    fig = px.pie(
        category_totals,
        values="Amount",
        names="Category",
        title="Spending by Category",
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")

    st.plotly_chart(fig, use_container_width=True)


def display_category_bar_chart(df: pd.DataFrame):
    """Display category breakdown as horizontal bar chart."""
    expenses_df = df[df["Amount"] < 0].copy()
    expenses_df["Amount"] = expenses_df["Amount"].abs()

    category_totals = expenses_df.groupby("Category")["Amount"].sum().reset_index()
    category_totals = category_totals.sort_values("Amount", ascending=True)

    fig = px.bar(
        category_totals,
        x="Amount",
        y="Category",
        orientation="h",
        title="Spending by Category",
        labels={"Amount": "Total Spent ($)", "Category": ""},
        color="Amount",
        color_continuous_scale="Reds"
    )

    st.plotly_chart(fig, use_container_width=True)


def convert_df_to_excel(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes for download."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Transactions")
    return output.getvalue()


# File uploader
uploaded_file = st.file_uploader(
    "Upload your bank statement (xlsx)",
    type=["xlsx"],
    help="Drag and drop your bank statement Excel file here"
)

if uploaded_file is not None:
    # Load and process data
    df = load_and_process_data(uploaded_file)

    if df is not None:
        st.success(f"Loaded {len(df)} transactions")

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

        # Editable transaction table
        st.header("Transaction Details")
        st.markdown("Edit categories in the table below. Changes will update the charts automatically.")

        # Create editable dataframe
        category_options = get_category_list()

        # Select columns to display and edit
        display_columns = ["Transaction Date", "Details", "Particulars", "Amount", "Type", "Category"]
        available_columns = [col for col in display_columns if col in df.columns]

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
                "Transaction Date": st.column_config.DateColumn(
                    "Date",
                    format="YYYY-MM-DD",
                ),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
        )

        # Update the main dataframe with edited categories
        df["Category"] = edited_df["Category"]

        # Download section
        st.header("Export Data")
        col1, col2 = st.columns([1, 3])

        with col1:
            excel_data = convert_df_to_excel(df)
            st.download_button(
                label="Download Categorized Data",
                data=excel_data,
                file_name="categorized_transactions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

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
            filtered_df = filtered_df[filtered_df["Category"].isin(selected_categories)]

        if type_filter == "Expenses":
            filtered_df = filtered_df[filtered_df["Amount"] < 0]
        elif type_filter == "Income":
            filtered_df = filtered_df[filtered_df["Amount"] > 0]

        if selected_months:
            filtered_df = filtered_df[filtered_df["Month"].isin(selected_months)]

        # Display filtered results
        st.dataframe(
            filtered_df[available_columns],
            hide_index=True,
            use_container_width=True,
        )

        st.caption(f"Showing {len(filtered_df)} of {len(df)} transactions")

else:
    st.info("Please upload a bank statement xlsx file to get started.")

    # Show expected format
    with st.expander("Expected file format"):
        st.markdown("""
        Your Excel file should contain the following columns:
        - **Transaction Date** - Date of the transaction
        - **Details** - Merchant/payee name (used for categorization)
        - **Particulars** - Additional details (optional, used for categorization)
        - **Amount** - Transaction amount (negative = expense, positive = income)
        - **Type** - Transaction type (Payment, Direct Debit, Deposit, etc.)
        """)
