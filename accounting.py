"""
accounting.py
-------------
All of the accounting logic for the app lives here (no Streamlit code).
It does five jobs:
  1. Loads the two CSV files and removes duplicate invoices.
  2. Turns every sale and every vendor invoice into journal-entry lines
     (this is the "full company" general ledger).
  3. Builds the 20 practice transactions (and their answer keys).
  4. Checks a student's journal entry against the answer key.
  5. Builds the trial balance, income statement and balance sheet.
"""

from pathlib import Path
import pandas as pd

# ---------------------------------------------------------------------------
# Company settings
# ---------------------------------------------------------------------------
COMPANY_NAME = "Lakeview Retail Co."           # fictional name shown on reports (change freely)
YEAR_END = pd.Timestamp("2025-12-31")          # last day of the data
PRACTICE_START = pd.Timestamp("2025-10-01")    # practice quarter = Q4 2025
PRACTICE_END = pd.Timestamp("2025-12-31")

# The company's balance sheet on January 1, 2024 (assumed, because the
# data files only contain transactions). Because the company spends far
# more on vendors than it earns, it needs a large starting cash balance.
OPENING_BALANCES = {          # positive = debit balance, negative = credit balance
    "Cash": 12_000_000.00,
    "Inventory": 3_000_000.00,
    "Owner's Capital": -15_000_000.00,
}

# name -> (type, normal balance side)
ACCOUNTS = {
    "Cash": ("Asset", "Debit"),
    "Inventory": ("Asset", "Debit"),
    "Accounts Payable": ("Liability", "Credit"),
    "Owner's Capital": ("Equity", "Credit"),
    "Retained Earnings": ("Equity", "Credit"),
    "Sales Revenue": ("Revenue", "Credit"),
    "Sales Discounts": ("Contra-revenue", "Debit"),
    "Cost of Goods Sold": ("Expense", "Debit"),
    "Marketing Expense": ("Expense", "Debit"),
    "Maintenance Expense": ("Expense", "Debit"),
    "Technology Expense": ("Expense", "Debit"),
    "Freight Expense": ("Expense", "Debit"),
    "Professional Services Expense": ("Expense", "Debit"),
    "Office Supplies Expense": ("Expense", "Debit"),
    "Utilities Expense": ("Expense", "Debit"),
}
EXPENSE_ACCOUNTS = [
    "Marketing Expense", "Maintenance Expense", "Technology Expense",
    "Freight Expense", "Professional Services Expense",
    "Office Supplies Expense", "Utilities Expense",
]
# Accounts a student can choose from when journalizing
JOURNAL_ACCOUNTS = [
    "Cash", "Inventory", "Accounts Payable", "Sales Revenue",
    "Sales Discounts", "Cost of Goods Sold",
] + EXPENSE_ACCOUNTS
BALANCE_SHEET_ACCOUNTS = ["Cash", "Inventory", "Accounts Payable",
                          "Owner's Capital", "Retained Earnings"]
NOMINAL_ACCOUNTS = ["Sales Revenue", "Sales Discounts", "Cost of Goods Sold"] + EXPENSE_ACCOUNTS
EXPENSE_NAME = {c: f"{c} Expense" for c in
                ["Marketing", "Maintenance", "Technology", "Freight",
                 "Professional Services", "Office Supplies", "Utilities"]}

SALES_FILE = "fictional_retail_sales_20000.csv"
AP_FILE = "fictional_accounts_payable_8000.csv"

# The hand-picked practice transactions
PRACTICE_SALES = [
    "SALE-013989",  # simple sale, no discount
    "SALE-018096",  # online, 2 units, no discount
    "SALE-003570",  # 5% discount
    "SALE-012969",  # 15% discount
    "SALE-017677",  # 20% discount
    "SALE-011583",  # 10% discount, thin profit (online)
    "SALE-019750",  # 10% discount, barely profitable
    "SALE-000673",  # 30% discount, small loss
    "SALE-018599",  # 10% discount, loss
    "SALE-014747",  # 35% discount, bigger loss (online)
]
PRACTICE_AP = [
    "INV-006940",  # paid 25 days early
    "INV-002823",  # paid 46 days early (60-day terms)
    "INV-003640",  # paid exactly on the due date
    "INV-003377",  # paid on time
    "INV-007027",  # paid 6 days late
    "INV-002009",  # paid 10 days late
    "INV-003426",  # paid 27 days late
    "INV-007748",  # paid 29 days late
    "INV-004309",  # overdue, unpaid
    "INV-004115",  # open (not yet due), unpaid
]


# ---------------------------------------------------------------------------
# 1. Loading the data
# ---------------------------------------------------------------------------
def load_data(data_dir):
    """Read both CSV files. Returns (sales, ap, number_of_duplicates_removed)."""
    data_dir = Path(data_dir)
    sales = pd.read_csv(data_dir / SALES_FILE, parse_dates=["sale_date"])
    ap = pd.read_csv(data_dir / AP_FILE,
                     parse_dates=["invoice_date", "due_date", "payment_date"])

    # Sales: work out the gross amount and the discount in dollars.
    # Cash received = net_sales; gross (what the price tags added up to)
    # = net_sales + discount, so the entry always balances to the penny.
    qp = (sales["quantity"] * sales["unit_price"]).round(2)
    disc = (qp - sales["net_sales"]).round(2).clip(lower=0)
    disc = disc.where(sales["discount_pct"] > 0, 0.0)
    sales["discount_amt"] = disc
    sales["gross_sales"] = (sales["net_sales"] + disc).round(2)

    # AP: the same invoice number appears twice for 12 invoices (same vendor,
    # same amount, billed again months later). Keep the first, drop the repeat.
    ap = ap.sort_values(["invoice_date", "record_id"])
    before = len(ap)
    ap = ap.drop_duplicates("invoice_number", keep="first").reset_index(drop=True)
    return sales, ap, before - len(ap)


# ---------------------------------------------------------------------------
# 2. The full-company ledger (every record -> journal lines)
# ---------------------------------------------------------------------------
def build_full_ledger(sales, ap):
    """One row per journal-entry line: date, account, debit, credit."""
    parts = []

    def add(dates, account, debit=None, credit=None):
        n = len(dates)
        parts.append(pd.DataFrame({
            "date": pd.to_datetime(dates).values,
            "account": account,
            "debit": debit.values if debit is not None else 0.0,
            "credit": credit.values if credit is not None else 0.0,
        }, index=range(n)))

    # Sales entry: Dr Cash, Dr Sales Discounts, Cr Sales Revenue
    add(sales["sale_date"], "Cash", debit=sales["net_sales"])
    has_disc = sales["discount_amt"] > 0
    add(sales.loc[has_disc, "sale_date"], "Sales Discounts",
        debit=sales.loc[has_disc, "discount_amt"])
    add(sales["sale_date"], "Sales Revenue", credit=sales["gross_sales"])
    # Cost of goods sold entry: Dr COGS, Cr Inventory
    add(sales["sale_date"], "Cost of Goods Sold", debit=sales["cost_of_goods_sold"])
    add(sales["sale_date"], "Inventory", credit=sales["cost_of_goods_sold"])

    # Vendor bill: Dr expense, Cr Accounts Payable
    for cat, name in EXPENSE_NAME.items():
        sub = ap[ap["expense_category"] == cat]
        if len(sub):
            add(sub["invoice_date"], name, debit=sub["invoice_amount"])
    add(ap["invoice_date"], "Accounts Payable", credit=ap["invoice_amount"])

    # Payment (only if made on or before 12/31/2025): Dr Accounts Payable, Cr Cash
    paid = ap[ap["payment_date"].notna() & (ap["payment_date"] <= YEAR_END)]
    add(paid["payment_date"], "Accounts Payable", debit=paid["invoice_amount"])
    add(paid["payment_date"], "Cash", credit=paid["invoice_amount"])

    lines = pd.concat(parts, ignore_index=True)
    lines["month"] = lines["date"].dt.to_period("M").astype(str)
    return lines


def _signed(lines):
    """Sum of (debit - credit) for each account."""
    if len(lines) == 0:
        return {}
    g = lines.groupby("account")[["debit", "credit"]].sum()
    return (g["debit"] - g["credit"]).round(2).to_dict()


def activity_between(lines, start, end):
    """Signed (debit - credit) activity per account from start to end (inclusive)."""
    mask = (lines["date"] >= pd.Timestamp(start)) & (lines["date"] <= pd.Timestamp(end))
    return _signed(lines[mask])


def balance_sheet_opening(lines, before_date):
    """
    Balance sheet accounts at the start of a period (the day before `before_date`).
    Revenue and expense results from earlier periods are rolled into Retained Earnings.
    """
    prior = _signed(lines[lines["date"] < pd.Timestamp(before_date)])
    bal = {a: 0.0 for a in BALANCE_SHEET_ACCOUNTS}
    for acct, amt in OPENING_BALANCES.items():
        bal[acct] += amt
    for acct, amt in prior.items():
        if acct in NOMINAL_ACCOUNTS:
            bal["Retained Earnings"] += amt
        else:
            bal[acct] += amt
    return {k: round(v, 2) for k, v in bal.items()}


# ---------------------------------------------------------------------------
# 5. Statements
# ---------------------------------------------------------------------------
def income_statement(activity):
    """activity = signed (debit - credit) per account for the period."""
    g = lambda a: activity.get(a, 0.0)
    gross = -g("Sales Revenue")
    disc = g("Sales Discounts")
    net_sales = gross - disc
    cogs = g("Cost of Goods Sold")
    exp = {a: g(a) for a in EXPENSE_ACCOUNTS if abs(g(a)) > 0.004}
    total_exp = sum(exp.values())
    gp = net_sales - cogs
    return {
        "gross_sales": round(gross, 2), "discounts": round(disc, 2),
        "net_sales": round(net_sales, 2), "cogs": round(cogs, 2),
        "gross_profit": round(gp, 2), "expenses": exp,
        "total_expenses": round(total_exp, 2),
        "net_income": round(gp - total_exp, 2),
    }


def balance_sheet(opening, activity):
    """
    opening: balance sheet accounts at the start (signed).
    activity: signed activity for the period (all accounts).
    Returns begin/end values, with net income for the period shown separately.
    """
    inc = income_statement(activity)
    end = {a: opening[a] + activity.get(a, 0.0) for a in BALANCE_SHEET_ACCOUNTS}
    return {
        "begin": {
            "cash": opening["Cash"], "inventory": opening["Inventory"],
            "ap": -opening["Accounts Payable"],
            "capital": -opening["Owner's Capital"],
            "re": -opening["Retained Earnings"], "ni": 0.0,
        },
        "end": {
            "cash": round(end["Cash"], 2), "inventory": round(end["Inventory"], 2),
            "ap": round(-end["Accounts Payable"], 2),
            "capital": round(-end["Owner's Capital"], 2),
            "re": round(-end["Retained Earnings"], 2),   # beginning retained earnings
            "ni": inc["net_income"],
        },
    }


def trial_balance(opening, activity):
    """Rows of (account, debit, credit) for accounts with a balance."""
    rows = []
    for acct in ACCOUNTS:
        bal = opening.get(acct, 0.0) + activity.get(acct, 0.0)
        bal = round(bal, 2)
        if abs(bal) < 0.005:
            continue
        rows.append((acct, bal if bal > 0 else 0.0, -bal if bal < 0 else 0.0))
    return rows


# ---------------------------------------------------------------------------
# 3. Practice transactions and answer keys
# ---------------------------------------------------------------------------
def _money(x):
    return f"${x:,.2f}"


def build_practice(sales, ap):
    """Returns (transactions, entries). Entries are numbered in date order."""
    txns = []
    srows = sales[sales["order_id"].isin(PRACTICE_SALES)].sort_values(["sale_date", "order_id"])
    for i, (_, r) in enumerate(srows.iterrows(), start=1):
        gp = round(r["net_sales"] - r["cost_of_goods_sold"], 2)
        sale_key = [("Cash", "Debit", r["net_sales"])]
        if r["discount_amt"] > 0:
            sale_key.append(("Sales Discounts", "Debit", r["discount_amt"]))
        sale_key.append(("Sales Revenue", "Credit", r["gross_sales"]))
        cogs_key = [("Cost of Goods Sold", "Debit", r["cost_of_goods_sold"]),
                    ("Inventory", "Credit", r["cost_of_goods_sold"])]

        if r["discount_pct"] == 0:
            take = (f"No discount, so the sale entry has just two lines. "
                    f"Gross profit on this sale was {_money(gp)}.")
        elif gp < 0:
            take = (f"A {r['discount_pct']:.0f}% discount pushed net sales ({_money(r['net_sales'])}) "
                    f"below the cost of the goods ({_money(r['cost_of_goods_sold'])}). "
                    f"Gross profit is a loss of {_money(-gp)}. Sales Discounts is a contra-revenue "
                    f"account: it reduces revenue without hiding the original price.")
        else:
            take = (f"With a {r['discount_pct']:.0f}% discount, revenue is recorded at the full price "
                    f"and the discount goes in its own account. Gross profit was {_money(gp)}.")

        sid = f"S{i}"
        txns.append({
            "txn_id": sid, "type": "sale", "number": i, "date": r["sale_date"],
            "title": f"{r['order_id']} · {r['product']} ×{int(r['quantity'])}",
            "short": f"{r['sale_date']:%m/%d} · {r['product']} ×{int(r['quantity'])}"
                     + (f" ({r['discount_pct']:.0f}% off)" if r["discount_pct"] > 0 else ""),
            "source": r.to_dict(), "takeaway": take,
            "entries": [
                {"entry_id": f"{sid}-1", "label": "Record the sale", "date": r["sale_date"],
                 "memo": f"Sale {r['order_id']}", "key": sale_key},
                {"entry_id": f"{sid}-2", "label": "Record the cost of goods sold", "date": r["sale_date"],
                 "memo": f"Cost of goods sold, {r['order_id']}", "key": cogs_key},
            ],
        })

    arows = ap[ap["invoice_number"].isin(PRACTICE_AP)].sort_values(["invoice_date", "invoice_number"])
    for i, (_, r) in enumerate(arows.iterrows(), start=1):
        acct = EXPENSE_NAME[r["expense_category"]]
        entries = [{"entry_id": f"A{i}-1", "label": "Record the vendor bill", "date": r["invoice_date"],
                    "memo": f"Invoice {r['invoice_number']}",
                    "key": [(acct, "Debit", r["invoice_amount"]),
                            ("Accounts Payable", "Credit", r["invoice_amount"])]}]
        paid = pd.notna(r["payment_date"]) and r["payment_date"] <= YEAR_END
        if paid:
            diff = int(r["days_early_late"])
            if diff < 0:
                when = f"{-diff} days early"
            elif diff == 0:
                when = "exactly on the due date"
            else:
                when = f"{diff} days late"
            take = (f"Paid {when}. The bill and the payment are two separate events: the bill "
                    f"creates the liability, the payment removes it. Either way, the expense "
                    f"belongs to the day the bill arrived, not the day it was paid.")
            entries.append({"entry_id": f"A{i}-2", "label": "Record the payment",
                            "date": r["payment_date"], "memo": f"Payment of {r['invoice_number']}",
                            "key": [("Accounts Payable", "Debit", r["invoice_amount"]),
                                    ("Cash", "Credit", r["invoice_amount"])]})
        else:
            status = "overdue" if r["status"] == "Overdue" else "open (not yet due)"
            take = (f"This invoice is {status} on 12/31/2025 and has no payment, so there is only "
                    f"one entry. The {_money(r['invoice_amount'])} stays in Accounts Payable and "
                    f"appears as a liability on the balance sheet, while the expense is already "
                    f"on the income statement.")
        txns.append({
            "txn_id": f"A{i}", "type": "ap", "number": i, "date": r["invoice_date"],
            "title": f"{r['invoice_number']} · {r['vendor_name'].split(' - ')[-1]}",
            "short": f"{r['invoice_date']:%m/%d} · {r['invoice_number']} · {r['expense_category']}"
                     + ("" if paid else f" ({r['status'].lower()})"),
            "source": r.to_dict(), "paid": paid, "takeaway": take, "entries": entries,
        })

    # Number every entry in date order (sales first on a tie)
    flat = [(e["date"], 0 if t["type"] == "sale" else 1, t["number"], e["entry_id"], e)
            for t in txns for e in t["entries"]]
    flat.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    for n, (_, _, _, _, e) in enumerate(flat, start=1):
        e["no"] = n
    entries = [x[4] for x in flat]
    return txns, entries


# ---------------------------------------------------------------------------
# 4. Checking a student's journal entry
# ---------------------------------------------------------------------------
def _cents(x):
    return int(round(float(x) * 100))


def check_entry(student_rows, key, attempt=1):
    """
    student_rows: list of (account, debit_amount, credit_amount) as typed by the student.
    key: list of (account, side, amount) from the answer key.
    Returns (is_correct, messages) where messages is a list of (level, text).
    level is one of "success", "info", "warning", "error".
    """
    msgs = []
    mine = []   # (line number, account, side, cents)
    for n, (acct, dr, cr) in enumerate(student_rows, start=1):
        dr_c, cr_c = _cents(dr or 0), _cents(cr or 0)
        if not acct and dr_c == 0 and cr_c == 0:
            continue                      # blank line
        if not acct:
            msgs.append(("error", f"Line {n}: you entered an amount but did not choose an account."))
            continue
        if dr_c > 0 and cr_c > 0:
            msgs.append(("error", f"Line {n} ({acct}): a line is either a debit or a credit, not both."))
            continue
        if dr_c == 0 and cr_c == 0:
            msgs.append(("error", f"Line {n} ({acct}): you chose an account but did not enter an amount."))
            continue
        mine.append((n, acct, "Debit" if dr_c > 0 else "Credit", dr_c if dr_c > 0 else cr_c))

    if msgs:
        return False, msgs
    if not mine:
        return False, [("info", "Choose accounts and enter amounts, then check your entry.")]

    tot_dr = sum(c for _, _, s, c in mine if s == "Debit")
    tot_cr = sum(c for _, _, s, c in mine if s == "Credit")
    if tot_dr != tot_cr:
        msgs.append(("warning", f"Debits ({_money(tot_dr / 100)}) do not equal credits "
                                f"({_money(tot_cr / 100)}). Every journal entry must balance."))

    key_left = [(a, s, _cents(m)) for a, s, m in key]
    wrong = []
    for n, acct, side, cents in mine:
        if (acct, side, cents) in key_left:
            key_left.remove((acct, side, cents))
            msgs.append(("success", f"Line {n} ({acct}, {side.lower()}): correct."))
        else:
            wrong.append((n, acct, side, cents))

    for n, acct, side, cents in wrong:
        same_acct_side = [k for k in key_left if k[0] == acct and k[1] == side]
        same_acct = [k for k in key_left if k[0] == acct]
        any_key_acct = any(k[0] == acct for k in key)
        if same_acct_side:
            msgs.append(("warning", f"Line {n} ({acct}, {side.lower()}): right account and side, "
                                    f"but check the amount."))
            key_left.remove(same_acct_side[0])
        elif same_acct:
            msgs.append(("warning", f"Line {n} ({acct}): this account is part of the entry, but "
                                    f"think again about whether it should be a debit or a credit."))
            key_left.remove(same_acct[0])
        elif any_key_acct:
            msgs.append(("warning", f"Line {n} ({acct}): this account is already used correctly "
                                    f"elsewhere in your entry. Check whether you repeated it."))
        else:
            msgs.append(("warning", f"Line {n} ({acct}): this account is not affected by this "
                                    f"transaction. Re-read the source document."))

    if key_left:
        n_missing = len(key_left)
        msgs.append(("info", f"Your entry is missing {n_missing} line{'s' if n_missing > 1 else ''}."))
        if attempt >= 2:
            names = sorted({a for a, _, _ in key_left})
            msgs.append(("info", "Hint: look for " + ", ".join(names) + " in this transaction."))

    correct = (not wrong) and (not key_left) and tot_dr == tot_cr
    if correct:
        msgs = [("success", "Correct! Every line matches and debits equal credits.")]
    return correct, msgs
