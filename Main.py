import streamlit as st
import pandas as pd


# Create tabs
uploaded_file = st.file_uploader("Upload Bank Statement")
tab1, tab2 = st.tabs(["Dashboard", "Dataset"])
with tab1:
    if uploaded_file:
        df = pd.read_excel(uploaded_file,header=6)
        
        # st.header("Dashboard")
        # st.write("Here you can add charts, KPIs, filters…")
        # st.bar_chart(df.groupby("Month")["Amount"].sum())
        # Convert 'Trans. Date' to datetime and extract Date/Time
        df['Trans. Date1'] = pd.to_datetime(df['Trans. Date'], format='%d %b %Y %H:%M:%S')
        df['Trans. Date'] = df['Trans. Date1'].dt.date
        df['Time'] = df['Trans. Date1'].dt.time

        # 7. Extract only the name from Description
        def extract_name(desc):
            desc = str(desc)
            # Check if 'from' or 'to' exists
            if 'from' in desc.lower():
                name = desc.lower().split('from')[1].split('|')[0].strip()
            elif 'to' in desc.lower():
                name = desc.lower().split('to')[1].split('|')[0].strip()
            else:
                name = desc.split('|')[0].strip()
            # Capitalize first letters
            return name.title()

        df['Transaction Name'] = df['Description'].apply(extract_name)

        # Handle Debit and Credit
        df['Debit(₦)'] = df['Debit(₦)'].replace('--', 0).replace(',', '', regex=True).astype(float)
        df['Credit(₦)'] = df['Credit(₦)'].replace('--', 0).replace(',', '', regex=True).astype(float)

        # Create transaction type and unified amount
        df['Transaction Type'] = df.apply(lambda x: 'Debit(₦)' if x['Debit(₦)'] > 0 else 'Credit(₦)', axis=1)
        df['Amount'] = df.apply(lambda x: x['Debit(₦)'] if x['Debit(₦)'] > 0 else x['Credit(₦)'], axis=1)
        df = df.drop(columns=['Debit(₦)', 'Credit(₦)'])

        # Split Description column
        desc_splits = df['Description'].str.split('|', expand=True)
        desc_columns = ['Transaction To/From', 'Platform', 'Account/Phone', 'Extra Info']
        desc_splits.columns = desc_columns[:desc_splits.shape[1]]

        # Correct swapped Platform and Account/Phone
        def fix_swap(row):
            platform = str(row['Platform']).strip()
            account = str(row['Account/Phone']).strip()
            
            # Check if Platform is mostly digits and Account/Phone is letters (network name)
            if platform.replace(' ', '').isdigit() and any(c.isalpha() for c in account):
                row['Platform'], row['Account/Phone'] = account, platform
            return row

        desc_splits = desc_splits.apply(fix_swap, axis=1)

        # Merge back into dataframe
        df = pd.concat([df, desc_splits], axis=1)
        df = df.drop(columns= "Value Date")

        # 8. Reorder columns
        cols_order = ['Transaction Reference', 'Trans. Date', 'Time', 'Transaction Type','Transaction To/From', 'Transaction Name', 'Account/Phone', 'Platform',   
                    'Channel', 'Extra Info', 'Amount','Balance After(₦)']
        df = df[cols_order]


        # Save cleaned CSV
        df.to_excel("3", index=False,engine="openpyxl")

        # print("Data cleaning complete. Sample data:")
        # print(df.iloc[73])

        def add_percentage_to_amount_table(df, amount_column='Amount'):
            table = df.copy()

            total_amount = table[amount_column].sum()

            if total_amount == 0:
                table['% of Total'] = 0
            else:
                table['% of Total'] = (
                    table[amount_column] / total_amount * 100
                ).round(2)

            return table


        def add_percentage_columns(pivot_df,
                                debit_col='Debit(₦)',
                                credit_col='Credit(₦)'):
            """
            Adds percentage contribution columns to a pivot table.
            Handles cases where totals are zero.
            """

            df = pivot_df.copy()

            # Ensure missing columns are handled safely
            if debit_col not in df.columns:
                df[debit_col] = 0

            if credit_col not in df.columns:
                df[credit_col] = 0

            # Calculate totals
            total_debit = df[debit_col].sum()
            total_credit = df[credit_col].sum()
            total_flow = total_debit + total_credit

            # Protect against division by zero
            if total_debit == 0:
                df['% Debit'] = 0
            else:
                df['% Debit'] = (df[debit_col] / total_debit * 100).round(2)

            if total_credit == 0:
                df['% Credit'] = 0
            else:
                df['% Credit'] = (df[credit_col] / total_credit * 100).round(2)

            if total_flow == 0:
                df['% Total Flow'] = 0
            else:
                df['% Total Flow'] = (
                    (df[debit_col] + df[credit_col]) / total_flow * 100
                ).round(2)

            return df

        import pandas as pd

        # Load cleaned dataset
        df = pd.read_excel("3")

        # Ensure Date column is datetime
        df['Trans. Date'] = pd.to_datetime(df['Trans. Date'])

        # Ensure Amount is numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

        # ========================================
        # 1️⃣ OVERALL FINANCIAL SUMMARY
        # ========================================

        total_debit = df.loc[df['Transaction Type'] == 'Debit(₦)', 'Amount'].sum()
        total_credit = df.loc[df['Transaction Type'] == 'Credit(₦)', 'Amount'].sum()

        total_debit_count = df[df['Transaction Type'] == 'Debit(₦)'].shape[0]
        total_credit_count = df[df['Transaction Type'] == 'Credit(₦)'].shape[0]
        latest_balance = df.sort_values(
            by='Trans. Date'
        ).iloc[-1]['Balance After(₦)']

        summary_df = pd.DataFrame({
            "Metric": [
                "Total Debit Amount",
                "Total Credit Amount",
                "Number of Debit Transactions",
                "Number of Credit Transactions",
                "Current Balance"
            ],
            "Value (₦)": [
                total_debit,
                total_credit,
                total_debit_count,
                total_credit_count,
                latest_balance
            ]
        })

        # ========================================
        # 2️⃣ MONTHLY CASH FLOW SUMMARY (January Format)
        # ========================================

        df['Month'] = df['Trans. Date'].dt.month_name()

        monthly_summary = df.pivot_table(
            index='Month',
            columns='Transaction Type',
            values='Amount',
            aggfunc='sum',
            fill_value=0
        )
        monthly_summary = add_percentage_columns(monthly_summary)

        # Ensure correct month order
        month_order = [
            "January","February","March","April","May","June",
            "July","August","September","October","November","December"
        ]

        monthly_summary = monthly_summary.reindex(month_order).dropna(how='all')

        # ========================================
        # 3️⃣ PLATFORM PERFORMANCE SUMMARY
        # ========================================

        platform_summary = df.pivot_table(
            index='Platform',
            columns='Transaction Type',
            values='Amount',
            aggfunc='sum',
            fill_value=0
        )
        platform_summary = add_percentage_columns(platform_summary)

        # ========================================
        # 4️⃣ DAILY TRANSACTION TREND (Better Format)
        # ========================================

        df['Date_Only'] = df['Trans. Date'].dt.date

        daily_summary = df.pivot_table(
            index='Date_Only',
            columns='Transaction Type',
            values='Amount',
            aggfunc='sum',
            fill_value=0
        ).sort_index()

        # ========================================
        # 5️⃣ TOP 10 SPENDING RECIPIENTS
        # ========================================
        import streamlit as st

        st.title("Top N spender/Recipient")

        number = st.number_input("Enter a number",value= 10)

        # st.write("You entered:", number)
        top_spending = (
            df[df['Transaction Type'] == 'Debit(₦)']
            .groupby('Transaction To/From')['Amount']
            .sum()
            .sort_values(ascending=False)
            .head(int(number))
            .reset_index()
        )
        top_spending = add_percentage_to_amount_table(top_spending)

        # ========================================
        # 6️⃣ TOP 10 INCOME SOURCES
        # ========================================

        top_income = (
            df[df['Transaction Type'] == 'Credit(₦)']
            .groupby('Transaction To/From')['Amount']
            .sum()
            .sort_values(ascending=False)
            .head(int(number))
            .reset_index()
        )
        top_income = add_percentage_to_amount_table(top_income)

        # ========================================
        # WRITE EVERYTHING INTO ONE EXCEL FILE
        # ========================================

        with pd.ExcelWriter(uploaded_file, engine="openpyxl") as writer:
            
            # Write cleaned data
            df.to_excel(writer, sheet_name="Cleaned_Data", index=False)
            
            start_row = 0
            
            # SECTION 1
            pd.DataFrame({"OVERALL FINANCIAL SUMMARY": []}).to_excel(writer, sheet_name="Analysis", startrow=start_row, index=False)
            summary_df.to_excel(writer, sheet_name="Analysis", startrow=start_row+1, index=False)
            start_row += len(summary_df) + 4
            
            # SECTION 2
            pd.DataFrame({"MONTHLY CASH FLOW SUMMARY": []}).to_excel(writer, sheet_name="Analysis", startrow=start_row, index=False)
            monthly_summary.to_excel(writer, sheet_name="Analysis", startrow=start_row+1)
            start_row += len(monthly_summary) + 4
            
            # SECTION 3
            pd.DataFrame({"PLATFORM PERFORMANCE SUMMARY": []}).to_excel(writer, sheet_name="Analysis", startrow=start_row, index=False)
            platform_summary.to_excel(writer, sheet_name="Analysis", startrow=start_row+1)
            start_row += len(platform_summary) + 4
            
            # SECTION 4
            pd.DataFrame({"DAILY TRANSACTION TREND": []}).to_excel(writer, sheet_name="Analysis", startrow=start_row, index=False)
            daily_summary.to_excel(writer, sheet_name="Analysis", startrow=start_row+1)
            start_row += len(daily_summary) + 4
            
            # SECTION 5
            pd.DataFrame({"TOP 10 SPENDING RECIPIENTS": []}).to_excel(writer, sheet_name="Analysis", startrow=start_row, index=False)
            top_spending.to_excel(writer, sheet_name="Analysis", startrow=start_row+1, index=False)
            start_row += len(top_spending) + 4
            
            # SECTION 6
            pd.DataFrame({"TOP 10 INCOME SOURCES": []}).to_excel(writer, sheet_name="Analysis", startrow=start_row, index=False)
            top_income.to_excel(writer, sheet_name="Analysis", startrow=start_row+1, index=False)

        # print("Analysis successfully written with improved formatting and Naira currency.")

        import pandas as pd

        # =========================
        # PROCESS SAVINGS SHEET
        # =========================

        try:
            # CHANGE THIS if your savings sheet has a different name
            savings_df = pd.read_excel(uploaded_file, sheet_name='Savings Account Transactions',header=6)
            savings_df = savings_df.drop(columns= "Value Date")

            # print("Savings sheet loaded successfully.")

            # Check if sheet is completely empty
            if savings_df.empty:
                pass
                # print("Savings sheet exists but has no rows. Skipping savings analysis.")
            else:
                # print(f"Savings sheet has {len(savings_df)} rows before cleaning.")

                # Strip column names (very important)
                savings_df.columns = savings_df.columns.str.strip()

                # print("Columns found:", savings_df.columns.tolist())

                # Expected columns
                required_columns = [
                    'Trans. Date',
                    'Description',
                    'Debit(₦)',
                    'Credit(₦)',
                    'Balance After(₦)',						
                    'Channel'	,
                    'Transaction Reference'

                ]

                # Validate required columns exist
                missing_cols = [col for col in required_columns if col not in savings_df.columns]
                if missing_cols:
                    pass
                    # print("Missing required columns:", missing_cols)
                    # print("Check your column names carefully (case-sensitive).")
                else:

                    # Work on a COPY to avoid SettingWithCopyWarning
                    df_savings = savings_df.copy()

                    # ----------------------------
                    # CLEAN DATE COLUMN
                    # ----------------------------
                    df_savings.loc[:, 'Trans. Date'] = pd.to_datetime(
                        df_savings['Trans. Date'],
                        errors='coerce'
                    )
                    # ----------------------------
                    # CLEAN NUMERIC COLUMNS
                    # ----------------------------
                    numeric_cols = ['Debit(₦)', 'Credit(₦)', 'Balance After(₦)']

                    for col in numeric_cols:
                        df_savings.loc[:, col] = (
                            df_savings[col]
                            .astype(str)
                            .str.replace(',', '', regex=False)
                            .replace('--', '0')
                        )

                        df_savings.loc[:, col] = pd.to_numeric(
                            df_savings[col],
                            errors='coerce'
                        ).fillna(0)

                    # Remove rows where Date is NaT
                    df_savings = df_savings[df_savings['Trans. Date'].notna()]

                    # print(f"Rows after cleaning: {len(df_savings)}")

                    if df_savings.empty:
                        pass
                        # print("All rows became invalid after cleaning. No savings sheets will be created.")
                    else:

                        # =========================
                        # TOTAL INTEREST
                        # =========================
                        interest_df = df_savings[
                            df_savings['Description'].str.contains(
                                'Interest',
                                case=False,
                                na=False
                            )
                        ]

                        total_interest = interest_df['Credit(₦)'].sum()

                        summary_df = pd.DataFrame({
                            'Metric': ['Total Interest Earned'],
                            'Value': [total_interest]
                        })

                        # print("Total interest calculated:", total_interest)

                        # =========================
                        # SAVINGS BALANCE (Latest)
                        # =========================
                        latest_balance = df_savings.sort_values(
                            by='Trans. Date'
                        ).iloc[-1]['Balance After(₦)']

                        balance_df = pd.DataFrame({
                            'Metric': ['Latest Savings Balance'],
                            'Value': [latest_balance]
                        })

                        # =========================
                        # INTEREST BY SAVINGS TYPE
                        # =========================
                        interest_by_type = (
                            interest_df
                            .groupby('Description')['Credit(₦)']
                            .sum()
                            .reset_index()
                        )

                        # =========================
                        # BALANCE BY SAVINGS TYPE
                        # =========================
                        balance_by_type = (
                            df_savings
                            .groupby('Description')['Balance After(₦)']
                            .max()
                            .reset_index()
                        )

        # =========================
        # WRITE EVERYTHING TO ONE SHEET
        # =========================

                    from openpyxl import load_workbook

                    sheet_name = "Savings_Analysis"

                    # Round currency properly
                    summary_df["Value"] = summary_df["Value"].round(2)
                    balance_df["Value"] = balance_df["Value"].round(2)

                    # Add section titles
                    summary_df.insert(0, "Section", "TOTAL INTEREST")
                    balance_df.insert(0, "Section", "LATEST SAVINGS BALANCE")
                    interest_by_type.insert(0, "Section", "INTEREST BY SAVINGS TYPE")
                    balance_by_type.insert(0, "Section", "BALANCE BY SAVINGS TYPE")

                    # Combine everything vertically
                    final_output = pd.concat(
                        [
                            summary_df,
                            pd.DataFrame([[]]),  # blank row
                            balance_df,
                            pd.DataFrame([[]]),
                            interest_by_type,
                            pd.DataFrame([[]]),
                            balance_by_type
                        ],
                        ignore_index=True
                    )

                    # Write ONCE
                    with pd.ExcelWriter(
                        uploaded_file,
                        engine="openpyxl",
                        mode="a",
                        if_sheet_exists="replace"
                    ) as writer:

                        final_output.to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False
                    )

                # print("Savings analysis successfully written to single sheet.")
                # print(f"{data["name"]}'s file is done")


        except Exception as e:
            # print("Error processing savings sheet:", e)
            pass
        from Dashboardcode import run_dashboard
    run_dashboard(uploaded_file)
with tab2:
    st.header("Raw Dataset")
    st.dataframe(df)  # Show the dataset
    # st.title("Bank Dashboard")
