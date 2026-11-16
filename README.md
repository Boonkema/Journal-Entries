# Journal Entry Lab

An interactive Streamlit app for entry-level accounting students. Students journalize
20 transactions (10 retail sales and 10 vendor invoices), post them to T-accounts, build a
trial balance, and see the income statement and balance sheet change. A company-wide page
shows the same statements built from every record in both data files.

## Files
- `app.py` - the Streamlit screens
- `accounting.py` - the accounting logic and answer keys
- `requirements.txt` - the Python packages Streamlit Cloud installs
- `data/` - the two CSV files (fictional data)

Run locally: `pip install -r requirements.txt` then `streamlit run app.py`
