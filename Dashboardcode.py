import streamlit as st
import pandas as pd
import plotly.express as px
import sys


# =========================================================
# FUNCTION: Extract Pivot Sections From "analysis sheet"
# =========================================================
def extract_sections(df):
    sections = {}
    current_section = None
    current_data = []

    for _, row in df.iterrows():
        first_cell = row[0]

        # Detect section title (single populated cell row)
        if pd.notna(first_cell) and row.count() == 1:
            if current_section and current_data:
                section_df = pd.DataFrame(current_data)
                section_df.columns = section_df.iloc[0]
                section_df = section_df[1:]
                sections[current_section.strip()] = section_df.reset_index(drop=True)

            current_section = first_cell.strip()
            current_data = []

        elif current_section:
            if row.isna().all():
                continue
            current_data.append(row.tolist())

    # Save last section
    if current_section and current_data:
        section_df = pd.DataFrame(current_data)
        section_df.columns = section_df.iloc[0]
        section_df = section_df[1:]
        sections[current_section.strip()] = section_df.reset_index(drop=True)

    return sections


# =========================================================
# MAIN DASHBOARD FUNCTION
# =========================================================

def run_dashboard(file_path: str,):
    """
    Launches the Streamlit dashboard using the
    'analysis sheet' from the provided Excel file.
    """

    st.set_page_config(page_title=f"Bank Statement Dashboard", layout="wide")
    st.title(f"Bank Statement Dashboard")

    # Load analysis sheet
    raw_df = pd.read_excel(file_path, sheet_name="Analysis", header=None)
    sections = extract_sections(raw_df)

    # -----------------------------------------------------
    # OVERALL FINANCIAL SUMMARY
    # -----------------------------------------------------
    if "OVERALL FINANCIAL SUMMARY" in sections:
        summary_df = sections["OVERALL FINANCIAL SUMMARY"]
        summary_df["Value (₦)"] = pd.to_numeric(
            summary_df["Value (₦)"], errors="coerce"
        )

        total_debit = summary_df.loc[
            summary_df["Metric"] == "Total Debit Amount", "Value (₦)"
        ].values[0]

        total_credit = summary_df.loc[
            summary_df["Metric"] == "Total Credit Amount", "Value (₦)"
        ].values[0]

        debit_count = summary_df.loc[
            summary_df["Metric"] == "Number of Debit Transactions", "Value (₦)"
        ].values[0]
        credit_count = summary_df.loc[
            summary_df["Metric"] == "Number of Credit Transactions", "Value (₦)"
        ].values[0]

        Current_Balance = summary_df.loc[
            summary_df["Metric"] == "Current Balance", "Value (₦)"
        ].values[0]

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Debit", f"₦{total_debit:,.2f}")
        col2.metric("Total Credit", f"₦{total_credit:,.2f}")
        col3.metric("Debit Transactions", int(debit_count))
        col4.metric("Credit Transactions", int(credit_count))
        col5.metric("Account Balance", f"₦{Current_Balance}")

    st.markdown("---")

    # -----------------------------------------------------
    # MONTHLY CASH FLOW SUMMARY
    # -----------------------------------------------------
    if "MONTHLY CASH FLOW SUMMARY" in sections:
        monthly_df = sections["MONTHLY CASH FLOW SUMMARY"]
        monthly_df["Credit(₦)"] = pd.to_numeric(
            monthly_df["Credit(₦)"], errors="coerce"
        )
        monthly_df["Debit(₦)"] = pd.to_numeric(
            monthly_df["Debit(₦)"], errors="coerce"
        )

        fig = px.bar(
            monthly_df,
            x="Month",
            y=["Credit(₦)", "Debit(₦)"],
            barmode="group",
            title="Monthly Cash Flow"
        )

        st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------
    # PLATFORM PERFORMANCE SUMMARY
    # -----------------------------------------------------
    if "PLATFORM PERFORMANCE SUMMARY" in sections:
        platform_df = sections["PLATFORM PERFORMANCE SUMMARY"]

        platform_df["Credit(₦)"] = pd.to_numeric(
            platform_df["Credit(₦)"], errors="coerce"
        )
        platform_df["Debit(₦)"] = pd.to_numeric(
            platform_df["Debit(₦)"], errors="coerce"
        )

        col1, col2 = st.columns(2)

        fig_credit = px.bar(
            platform_df,
            x="Credit(₦)",
            y="Platform",
            orientation="h",
            title="Credit by Platform"
        )

        fig_debit = px.bar(
            platform_df,
            x="Debit(₦)",
            y="Platform",
            orientation="h",
            title="Debit by Platform"
        )

        col1.plotly_chart(fig_credit, use_container_width=True)
        col2.plotly_chart(fig_debit, use_container_width=True)

    # -----------------------------------------------------
    # TOP 10 SPENDING RECIPIENTS
    # -----------------------------------------------------
    if "TOP 10 SPENDING RECIPIENTS" in sections:
        spending_df = sections["TOP 10 SPENDING RECIPIENTS"].copy()
        spending_df["Amount"] = pd.to_numeric(spending_df["Amount"], errors="coerce")

        spending_df = spending_df.sort_values("Amount", ascending=True)

        st.markdown("---")
        st.subheader("Top 10 Spending Recipients")

        fig_spending = px.bar(
            spending_df,
            x="Amount",
            y="Transaction To/From",
            orientation="h",
            title="Spending by Recipient (₦)"
        )

        st.plotly_chart(fig_spending, use_container_width=True)

    # -----------------------------------------------------
    # TOP 10 INCOME SOURCES
    # -----------------------------------------------------
    if "TOP 10 INCOME SOURCES" in sections:
        income_df = sections["TOP 10 INCOME SOURCES"].copy()
        income_df["Amount"] = pd.to_numeric(income_df["Amount"], errors="coerce")

        income_df = income_df.sort_values("Amount", ascending=True)

        st.markdown("---")
        st.subheader("Top 10 Income Sources")

        fig_income = px.bar(
            income_df,
            x="Amount",
            y="Transaction To/From",
            orientation="h",
            title="Income by Source (₦)"
        )

        st.plotly_chart(fig_income, use_container_width=True)

    if "DAILY TRANSACTION TREND" in sections:
        Daily_df = sections["DAILY TRANSACTION TREND"]
        Daily_df["Credit(₦)"] = pd.to_numeric(
            Daily_df["Credit(₦)"], errors="coerce"
        )
        Daily_df["Debit(₦)"] = pd.to_numeric(
            Daily_df["Debit(₦)"], errors="coerce"
        )

        fig = px.line(
            Daily_df,
            x="Date_Only",
            y=["Credit(₦)", "Debit(₦)"],
            title="Daily Trend"
            
        )

        st.plotly_chart(fig, use_container_width=True)

output_path = sys.argv[1] if len(sys.argv) > 1 else "default_path"
if __name__ == "__main__":
    run_dashboard(output_path)