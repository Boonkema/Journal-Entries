"""
Journal Entry Lab  (Streamlit app)
----------------------------------
Students journalize 20 real-looking transactions (10 retail sales and 10 vendor
invoices), post them to T-accounts, build a trial balance, and watch the income
statement and balance sheet change. A company-wide page shows the same
statements built from every record in both data files.

All accounting logic is in accounting.py. This file only draws the screens.
"""

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st

import accounting as ac

st.set_page_config(page_title="Journal Entry Lab", page_icon="📒", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
CAPITAL = -ac.OPENING_BALANCES["Owner's Capital"]   # owners' starting investment (positive number)

PAGES = [
    "Start here",
    "1 · Journalize",
    "2 · Post to T-accounts",
    "3 · Trial balance",
    "4 · Financial statements",
    "Company-wide view",
]

# ---------------------------------------------------------------------------
# Look and feel (colors are semi-transparent so they work in light and dark mode)
# ---------------------------------------------------------------------------
CSS = """
<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
.tacct {border: 1px solid rgba(128,128,128,.5); border-radius: 6px; margin-bottom: 14px;
        overflow: hidden; font-variant-numeric: tabular-nums;}
.tacct .t-name {text-align: center; font-weight: 600; padding: 6px 8px;
        border-bottom: 2px solid rgba(128,128,128,.85); background: rgba(128,128,128,.10);}
.tacct .t-body {display: flex;}
.tacct .t-col {flex: 1; min-height: 58px; padding: 4px 8px;}
.tacct .t-col.dr {border-right: 2px solid rgba(128,128,128,.85);}
.tacct .t-head {font-size: .75rem; opacity: .65; padding-bottom: 2px;}
.tacct .trow {display: flex; justify-content: space-between; gap: 8px; font-size: .88rem;
        padding: 1px 3px; border-radius: 3px;}
.tacct .trow.new {background: rgba(46,160,67,.30); font-weight: 600;}
.tacct .t-bal {border-top: 1px solid rgba(128,128,128,.6); padding: 5px 10px; text-align: right;
        font-weight: 600; font-size: .9rem;}
.jtable, .stmt table, .ttable {width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums;}
.jtable th, .ttable th {text-align: left; font-weight: 600; font-size: .85rem; opacity: .75;
        border-bottom: 2px solid rgba(128,128,128,.6); padding: 4px 8px;}
.jtable td, .ttable td {padding: 3px 8px;}
.jtable td.num, .ttable td.num, .jtable th.num, .ttable th.num {text-align: right;}
.jtable tr.firstline td {border-top: 1px solid rgba(128,128,128,.3);}
.jtable td.cr-acct {padding-left: 36px;}
.jtable td.memo {font-style: italic; opacity: .7; padding-left: 36px; font-size: .85rem;}
.ttable tr.total td {border-top: 1px solid rgba(128,128,128,.8); border-bottom: 3px double rgba(128,128,128,.8);
        font-weight: 700;}
.stmt {margin-bottom: 8px;}
.stmt .stmt-title {font-size: 1.15rem; font-weight: 700;}
.stmt .stmt-sub {opacity: .7; margin-bottom: 6px; font-size: .9rem;}
.stmt th {text-align: right; font-size: .85rem; opacity: .75; border-bottom: 2px solid rgba(128,128,128,.6);
        padding: 4px 8px;}
.stmt td {padding: 3px 8px;}
.stmt td.num {text-align: right;}
.stmt tr.s-h td {font-weight: 700; padding-top: 10px;}
.stmt tr.s-i td:first-child {padding-left: 24px;}
.stmt tr.s-t td {border-top: 1px solid rgba(128,128,128,.8); font-weight: 600;}
.stmt tr.s-g td {border-top: 1px solid rgba(128,128,128,.8); border-bottom: 3px double rgba(128,128,128,.8);
        font-weight: 700;}
.doc {border: 1px solid rgba(128,128,128,.5); border-radius: 6px; padding: 14px 16px; margin-bottom: 12px;
        background: rgba(128,128,128,.06);}
.doc .doc-title {font-weight: 700; font-size: 1.05rem; margin-bottom: 2px;}
.doc .doc-meta {opacity: .7; font-size: .85rem; margin-bottom: 8px;}
.doc table {width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums;}
.doc td {padding: 3px 0;}
.doc td.num {text-align: right;}
.doc tr.line-top td {border-top: 1px solid rgba(128,128,128,.5);}
.doc tr.bold td {font-weight: 700;}
.doc .doc-note {margin-top: 8px; font-size: .85rem; opacity: .8;}
</style>
"""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def fmt(x):
    """1234.5 -> 1,234.50   -50 -> (50.00)   0 -> –"""
    if x is None:
        return ""
    if abs(x) < 0.005:
        return "–"
    s = f"{abs(x):,.2f}"
    return f"({s})" if x < 0 else s


def money(x):
    return f"${x:,.2f}"


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def statement_html(title, subtitle, headers, rows):
    """rows = list of (label, [values] or None, style); style: h, i, n, t, g"""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for label, vals, style in rows:
        vals = vals if vals else [None] * len(headers)
        cells = "".join(f'<td class="num">{fmt(v) if v is not None else ""}</td>' for v in vals)
        body.append(f'<tr class="s-{style}"><td>{label}</td>{cells}</tr>')
    return (f'<div class="stmt"><div class="stmt-title">{title}</div>'
            f'<div class="stmt-sub">{subtitle}</div><table><thead><tr><th></th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def income_rows(inc):
    rows = [
        ("Sales revenue", [inc["gross_sales"]], "i"),
        ("Less: sales discounts", [inc["discounts"]], "i"),
        ("Net sales", [inc["net_sales"]], "t"),
        ("Less: cost of goods sold", [inc["cogs"]], "i"),
        ("Gross profit", [inc["gross_profit"]], "t"),
        ("Operating expenses", None, "h"),
    ]
    for acct, amt in inc["expenses"].items():
        rows.append((acct, [amt], "i"))
    rows.append(("Total operating expenses", [inc["total_expenses"]], "t"))
    rows.append(("Net income (loss)", [inc["net_income"]], "g"))
    return rows


def balance_rows(bs):
    b, e = bs["begin"], bs["end"]

    def line(label, key, style="i"):
        return (label, [b[key], e[key] - b[key], e[key]], style)

    def total(label, keys, style="t"):
        tb = sum(b[k] for k in keys)
        te = sum(e[k] for k in keys)
        return (label, [tb, te - tb, te], style)

    rows = [
        ("Assets", None, "h"),
        line("Cash", "cash"), line("Inventory", "inventory"),
        total("Total assets", ["cash", "inventory"]),
        ("Liabilities", None, "h"),
        line("Accounts payable", "ap"),
        total("Total liabilities", ["ap"]),
        ("Owner's equity", None, "h"),
        line("Owner's capital", "capital"),
        line("Retained earnings, beginning of period", "re"),
        line("Net income (loss) for the period", "ni"),
        total("Total owner's equity", ["capital", "re", "ni"]),
        total("Total liabilities and owner's equity", ["ap", "capital", "re", "ni"], "g"),
    ]
    assets_end = e["cash"] + e["inventory"]
    le_end = e["ap"] + e["capital"] + e["re"] + e["ni"]
    return rows, abs(assets_end - le_end) < 0.005, assets_end, le_end


def trial_balance_html(rows):
    body = "".join(f'<tr><td>{a}</td><td class="num">{fmt(d) if d else ""}</td>'
                   f'<td class="num">{fmt(c) if c else ""}</td></tr>' for a, d, c in rows)
    td = sum(r[1] for r in rows)
    tc = sum(r[2] for r in rows)
    body += f'<tr class="total"><td>Totals</td><td class="num">{fmt(td)}</td><td class="num">{fmt(tc)}</td></tr>'
    return (f'<table class="ttable"><thead><tr><th>Account</th><th class="num">Debit</th>'
            f'<th class="num">Credit</th></tr></thead><tbody>{body}</tbody></table>'), td, tc


def journal_html(entry_list):
    """General journal layout: debits first, credits indented."""
    rows = []
    for e in entry_list:
        lines = sorted(e["key"], key=lambda k: 0 if k[1] == "Debit" else 1)
        for i, (acct, side, amt) in enumerate(lines):
            first = ' class="firstline"' if i == 0 else ""
            date = f"{e['date']:%m/%d/%Y}" if i == 0 else ""
            no = f"#{e['no']}" if i == 0 else ""
            acct_cls = "" if side == "Debit" else ' class="cr-acct"'
            dr = fmt(amt) if side == "Debit" else ""
            cr = fmt(amt) if side == "Credit" else ""
            rows.append(f'<tr{first}><td>{no}</td><td>{date}</td><td{acct_cls}>{acct}</td>'
                        f'<td class="num">{dr}</td><td class="num">{cr}</td></tr>')
        rows.append(f'<tr><td></td><td></td><td class="memo">({e["memo"]})</td><td></td><td></td></tr>')
    return ('<table class="jtable"><thead><tr><th>No.</th><th>Date</th><th>Account</th>'
            '<th class="num">Debit</th><th class="num">Credit</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def t_account_html(acct, opening, lines, new_id=None):
    dr_rows, cr_rows = [], []
    if abs(opening) > 0.004:
        (dr_rows if opening > 0 else cr_rows).append(("Beg. bal.", abs(opening), False))
    bal = opening
    for ln in lines:
        is_new = ln["entry_id"] == new_id
        if ln["side"] == "Debit":
            dr_rows.append((f"#{ln['no']}", ln["amount"], is_new))
            bal += ln["amount"]
        else:
            cr_rows.append((f"#{ln['no']}", ln["amount"], is_new))
            bal -= ln["amount"]

    def col(rows):
        return "".join(f'<div class="trow{" new" if n else ""}"><span>{lab}</span>'
                       f'<span>{fmt(amt)}</span></div>' for lab, amt, n in rows)

    if abs(bal) < 0.005:
        bal_text = "Balance: 0.00"
    else:
        bal_text = f"Balance: {abs(bal):,.2f} {'debit' if bal > 0 else 'credit'}"
    return (f'<div class="tacct"><div class="t-name">{acct}</div><div class="t-body">'
            f'<div class="t-col dr"><div class="t-head">Debit</div>{col(dr_rows)}</div>'
            f'<div class="t-col"><div class="t-head">Credit</div>{col(cr_rows)}</div></div>'
            f'<div class="t-bal">{bal_text}</div></div>')


def sale_doc_html(r):
    disc_row = ""
    if r["discount_amt"] > 0:
        disc_row = (f'<tr><td>Discount ({r["discount_pct"]:.0f}%)</td><td></td>'
                    f'<td class="num">−{r["discount_amt"]:,.2f}</td></tr>')
    return (f'<div class="doc"><div class="doc-title">Sales receipt</div>'
            f'<div class="doc-meta">{r["order_id"]} · {r["sale_datetime"]} · Store {r["store_id"]}, '
            f'{r["city"]} · {r["channel"]}</div><table>'
            f'<tr><td>{r["product"]}</td><td>{int(r["quantity"])} × {r["unit_price"]:,.2f}</td>'
            f'<td class="num">{r["gross_sales"]:,.2f}</td></tr>{disc_row}'
            f'<tr class="line-top bold"><td>Total paid by customer</td><td></td>'
            f'<td class="num">{r["net_sales"]:,.2f}</td></tr></table>'
            f'<div class="doc-note">Paid by {r["payment_method"].lower()} (treat every payment as cash).<br>'
            f'Cost of these items in the inventory records: <b>{money(r["cost_of_goods_sold"])}</b></div></div>')


def invoice_doc_html(t):
    r = t["source"]
    rows = [
        ("Invoice number", r["invoice_number"]),
        ("Vendor", r["vendor_name"]),
        ("Department", r["department"]),
        ("Expense type", r["expense_category"]),
        ("Invoice date", f"{r['invoice_date']:%m/%d/%Y}"),
        ("Terms", f"Net {int(r['payment_terms_days'])} days, due {r['due_date']:%m/%d/%Y}"),
    ]
    body = "".join(f"<tr><td>{k}</td><td class='num'>{v}</td></tr>" for k, v in rows)
    body += (f'<tr class="line-top bold"><td>Amount due</td>'
             f'<td class="num">{money(r["invoice_amount"])}</td></tr>')
    if t["paid"]:
        note = (f'Payment record: paid on <b>{r["payment_date"]:%m/%d/%Y}</b> by '
                f'{r["payment_method"].lower()} (treat every payment as cash).')
    else:
        note = (f'Payment record: <b>no payment</b> recorded through 12/31/2025 '
                f'(status: {r["status"].lower()}).')
    return (f'<div class="doc"><div class="doc-title">Vendor invoice</div>'
            f'<div class="doc-meta">Accounts payable file</div><table>{body}</table>'
            f'<div class="doc-note">{note}</div></div>')


# ---------------------------------------------------------------------------
# Data (loaded once and reused)
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading the company data…")
def load_everything():
    sales, ap, removed = ac.load_data(DATA_DIR)
    lines = ac.build_full_ledger(sales, ap)
    txns, entries = ac.build_practice(sales, ap)
    opening = ac.balance_sheet_opening(lines, ac.PRACTICE_START)

    nominal = lines[lines["account"].isin(ac.NOMINAL_ACCOUNTS)]
    net_income = (nominal["credit"] - nominal["debit"]).groupby(nominal["month"]).sum()
    cash = lines[lines["account"] == "Cash"]
    cash_month = (cash["debit"] - cash["credit"]).groupby(cash["month"]).sum().cumsum() \
        + ac.OPENING_BALANCES["Cash"]
    monthly = pd.DataFrame({"Net income (loss)": net_income, "Cash at month end": cash_month}).round(2)
    return sales, ap, removed, lines, txns, entries, opening, monthly


for needed in (ac.SALES_FILE, ac.AP_FILE):
    if not (DATA_DIR / needed).exists():
        st.error(f"The data file **{needed}** was not found. It must be inside a folder named "
                 f"**data** next to app.py in your GitHub repository.")
        st.stop()

SALES, AP, REMOVED, LINES, TXNS, ENTRIES, OPENING, MONTHLY = load_everything()
ENTRY_BY_ID = {e["entry_id"]: e for e in ENTRIES}
N_ENTRIES = len(ENTRIES)

# ---------------------------------------------------------------------------
# Student progress (kept in session_state)
# ---------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("page", PAGES[0])
ss.setdefault("done", {})         # entry_id -> "correct" or "revealed"
ss.setdefault("posted", [])       # entry_ids in the order they were posted
ss.setdefault("attempts", {})     # entry_id -> number of tries
ss.setdefault("feedback", {})     # entry_id -> list of (level, message)
ss.setdefault("last_posted", None)


def reset_all():
    st.session_state.clear()


def go(page):
    st.session_state.page = page


def post_entry(entry_id):
    if entry_id and entry_id not in st.session_state.posted:
        st.session_state.posted.append(entry_id)
        st.session_state.last_posted = entry_id


def post_all(entry_ids):
    for eid in entry_ids:
        if eid not in st.session_state.posted:
            st.session_state.posted.append(eid)
    st.session_state.last_posted = None


def reveal(entry_id):
    st.session_state.done[entry_id] = "revealed"


def practice_activity():
    """Signed (debit - credit) totals per account from the entries the student has posted."""
    act = {}
    for eid in ss.posted:
        for acct, side, amt in ENTRY_BY_ID[eid]["key"]:
            act[acct] = act.get(acct, 0.0) + (amt if side == "Debit" else -amt)
    return {k: round(v, 2) for k, v in act.items()}


def show_messages(messages):
    for level, text in messages:
        {"success": st.success, "info": st.info, "warning": st.warning, "error": st.error}[level](text)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
html(CSS)
with st.sidebar:
    st.subheader("Your progress")
    st.progress(len(ss.done) / N_ENTRIES, text=f"Journalized: {len(ss.done)} of {N_ENTRIES} entries")
    st.progress(len(ss.posted) / N_ENTRIES, text=f"Posted: {len(ss.posted)} of {N_ENTRIES} entries")
    revealed = sum(1 for v in ss.done.values() if v == "revealed")
    if revealed:
        st.caption(f"You used the answer key on {revealed} entr{'y' if revealed == 1 else 'ies'}.")
    st.button("Start over", on_click=reset_all, help="Clears all of your entries and postings.")
    with st.expander("Chart of accounts"):
        rows = ["| Account | Type | Normal balance |", "|---|---|---|"]
        for name, (typ, side) in ac.ACCOUNTS.items():
            rows.append(f"| {name} | {typ} | {side} |")
        st.markdown("\n".join(rows))
    with st.expander("Debit and credit rules"):
        st.markdown(
            "- **Assets** and **expenses** go up with a **debit**, down with a credit.\n"
            "- **Liabilities**, **equity** and **revenue** go up with a **credit**, down with a debit.\n"
            "- **Sales Discounts** is a contra-revenue account: it works like an expense (debit to increase).\n"
            "- Total debits must always equal total credits.")

# ---------------------------------------------------------------------------
# Header and navigation
# ---------------------------------------------------------------------------
st.title("📒 Journal Entry Lab")
st.radio("Page", PAGES, horizontal=True, key="page", label_visibility="collapsed")
st.divider()
page = ss.page


# ===========================================================================
# PAGE: Start here
# ===========================================================================
def page_start():
    st.header("Follow a struggling company through the accounting cycle")
    st.write(
        "You are the accountant for a retail company that sells technology, furniture and office "
        "products in 12 stores and online. Customers pay when they buy, and vendors send bills that "
        "the company pays later. Your job for the fourth quarter of 2025 (October 1 to December 31) "
        "is to record what happened and see how it changes the company's financial statements."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("What you will do")
        st.markdown(
            "**1 · Journalize.** Read a source document (a sales receipt or a vendor invoice), choose the "
            "accounts, and enter the debits and credits. You get instant feedback from the answer key.\n\n"
            "**2 · Post to T-accounts.** Copy each journal entry into the ledger and watch the "
            "account balances move.\n\n"
            "**3 · Trial balance.** Check that total debits equal total credits.\n\n"
            "**4 · Financial statements.** See the income statement and balance sheet, with the "
            "balance sheet showing where you started, what your entries changed, and where you ended.\n\n"
            "**Company-wide view.** The same statements built from every sale and invoice in both "
            "years, so you can see where your 20 transactions fit in."
        )
    with c2:
        st.subheader("Your practice set")
        st.markdown(
            f"- **10 retail sales.** Each has two entries: one for the sale and one for the cost of the "
            f"goods sold. The set includes sales with no discount, small and large discounts, and "
            f"sales that lost money.\n"
            f"- **10 vendor invoices.** Each has a bill entry. Invoices that were paid also have a "
            f"payment entry. Some were paid early, on time or late, and two are still unpaid "
            f"(one overdue, one not yet due).\n"
            f"- **{N_ENTRIES} entries in total**, numbered in date order.\n\n"
            f"Ready? Choose **1 · Journalize** above, or use the button below."
        )
        st.button("Start journalizing", on_click=go, args=(PAGES[1],), type="primary")

    with st.expander("Assumptions behind this company"):
        st.markdown(
            "- The data files only contain transactions, so the company's **starting balance sheet on "
            f"January 1, 2024 is assumed**: cash {money(ac.OPENING_BALANCES['Cash'])}, inventory "
            f"{money(ac.OPENING_BALANCES['Inventory'])}, and owner's capital "
            f"{money(CAPITAL)}.\n"
            "- Every payment method (cash, cards, digital wallets, ACH, checks) is treated as **cash**.\n"
            "- The company never buys inventory in this data, so inventory only goes down.\n"
            "- An expense is recorded when the vendor bill is dated, not when it is paid.\n"
            "- A payment dated after December 31, 2025 is not recorded, so that bill stays in Accounts Payable.\n"
            f"- **{REMOVED} duplicate vendor invoices** (the same invoice number billed twice) were removed "
            "from the data before anything was calculated.\n"
            "- Your practice quarter starts with the company's real balances as of September 30, 2025, "
            "calculated from all earlier transactions."
        )


# ===========================================================================
# PAGE: 1 · Journalize
# ===========================================================================
def entry_form(e):
    eid = e["entry_id"]
    st.markdown(f"**Entry #{e['no']}: {e['label']}**  ·  {e['date']:%m/%d/%Y}")

    if eid in ss.done:
        if ss.done[eid] == "correct":
            st.success("Journalized correctly.")
        else:
            st.info("Answer shown. Study it, then move on to the next entry.")
        html(journal_html([e]))
        return

    options = [""] + ac.JOURNAL_ACCOUNTS
    with st.form(f"form_{eid}"):
        h1, h2, h3 = st.columns([3, 1.3, 1.3])
        h1.markdown("**Account**")
        h2.markdown("**Debit**")
        h3.markdown("**Credit**")
        rows = []
        for i in range(4):
            c1, c2, c3 = st.columns([3, 1.3, 1.3])
            acct = c1.selectbox(f"Account, line {i + 1}", options, key=f"acct_{eid}_{i}",
                                format_func=lambda x: x if x else "Choose an account",
                                label_visibility="collapsed")
            dr = c2.number_input(f"Debit, line {i + 1}", min_value=0.0, value=None, step=0.01,
                                 format="%.2f", placeholder="0.00", key=f"dr_{eid}_{i}",
                                 label_visibility="collapsed")
            cr = c3.number_input(f"Credit, line {i + 1}", min_value=0.0, value=None, step=0.01,
                                 format="%.2f", placeholder="0.00", key=f"cr_{eid}_{i}",
                                 label_visibility="collapsed")
            rows.append((acct, dr, cr))
        st.caption("Enter debit lines first, then credit lines. Leave unused lines blank.")
        submitted = st.form_submit_button("Check my entry", type="primary")

    if submitted:
        if any(a or d or c for a, d, c in rows):
            ss.attempts[eid] = ss.attempts.get(eid, 0) + 1
        ok, msgs = ac.check_entry(rows, e["key"], ss.attempts.get(eid, 1))
        ss.feedback[eid] = msgs
        if ok:
            ss.done[eid] = "correct"
            st.rerun()

    if ss.feedback.get(eid):
        show_messages(ss.feedback[eid])
    if ss.attempts.get(eid, 0) >= 3:
        st.button("Show me the answer", key=f"reveal_{eid}", on_click=reveal, args=(eid,))


def page_journalize():
    st.header("Step 1: Journalize")
    st.write("Pick a transaction, read the source document, and record each entry. "
             "A ✅ means every entry for that transaction is done.")

    kind = st.radio("Type of transaction", ["Retail sales", "Vendor invoices"], horizontal=True)
    want = "sale" if kind == "Retail sales" else "ap"
    group = [t for t in TXNS if t["type"] == want]

    def label(tid):
        t = next(x for x in group if x["txn_id"] == tid)
        n_done = sum(1 for e in t["entries"] if e["entry_id"] in ss.done)
        icon = "✅" if n_done == len(t["entries"]) else ("🟡" if n_done else "⬜")
        return f"{icon}  {t['short']}"

    tid = st.selectbox("Choose a transaction", [t["txn_id"] for t in group],
                       format_func=label, key=f"txn_pick_{want}")
    t = next(x for x in group if x["txn_id"] == tid)

    left, right = st.columns([2, 3], gap="large")
    with left:
        st.subheader("Source document")
        html(sale_doc_html(t["source"]) if t["type"] == "sale" else invoice_doc_html(t))
        if t["type"] == "ap" and not t["paid"]:
            st.caption("This invoice has no payment, so there is only one entry to record.")
    with right:
        st.subheader("Your journal entries")
        for e in t["entries"]:
            with st.container(border=True):
                entry_form(e)
        if all(e["entry_id"] in ss.done for e in t["entries"]):
            st.info("💡 " + t["takeaway"])

    st.divider()
    n_ready = len([e for e in ENTRIES if e["entry_id"] in ss.done and e["entry_id"] not in ss.posted])
    c1, c2 = st.columns([3, 2])
    with c1:
        with st.expander(f"General journal so far ({len(ss.done)} entries)"):
            done_entries = [e for e in ENTRIES if e["entry_id"] in ss.done]
            if done_entries:
                html(journal_html(done_entries))
            else:
                st.write("Entries you journalize correctly will appear here.")
    with c2:
        if n_ready:
            st.button(f"Continue to step 2: post {n_ready} entr{'y' if n_ready == 1 else 'ies'}",
                      on_click=go, args=(PAGES[2],), type="primary")


# ===========================================================================
# PAGE: 2 · Post to T-accounts
# ===========================================================================
def ledger_lines():
    """For each account, the posted lines in the order they were posted."""
    by_acct = {}
    for eid in ss.posted:
        e = ENTRY_BY_ID[eid]
        for acct, side, amt in e["key"]:
            by_acct.setdefault(acct, []).append(
                {"no": e["no"], "side": side, "amount": amt, "entry_id": eid})
    return by_acct


def page_post():
    st.header("Step 2: Post to T-accounts")
    st.write("Posting copies each line of a journal entry into the matching T-account. "
             "Debits go on the left, credits on the right.")

    ready = [e for e in ENTRIES if e["entry_id"] in ss.done and e["entry_id"] not in ss.posted]
    m1, m2, m3 = st.columns(3)
    m1.metric("Journalized", f"{len(ss.done)} of {N_ENTRIES}")
    m2.metric("Posted", f"{len(ss.posted)} of {N_ENTRIES}")
    m3.metric("Ready to post", len(ready))

    if not ss.done:
        st.info("Journalize at least one entry in step 1, then come back to post it.")
        return

    if ready:
        c1, c2, c3 = st.columns([4, 1.6, 1.8])
        pick = c1.selectbox(
            "Choose an entry to post", [e["entry_id"] for e in ready], key="post_pick",
            format_func=lambda i: f"#{ENTRY_BY_ID[i]['no']} · {ENTRY_BY_ID[i]['date']:%m/%d} · "
                                  f"{ENTRY_BY_ID[i]['memo']}")
        c2.write("")
        c2.button("Post this entry", on_click=post_entry, args=(pick,), type="primary")
        c3.write("")
        c3.button(f"Post all {len(ready)} ready", on_click=post_all,
                  args=([e["entry_id"] for e in ready],))
    elif len(ss.posted) < N_ENTRIES:
        st.success("Everything you have journalized is posted. Journalize more entries in step 1 to keep going.")

    by_acct = ledger_lines()

    if ss.last_posted and ss.last_posted in ENTRY_BY_ID and ss.last_posted in ss.posted:
        e = ENTRY_BY_ID[ss.last_posted]
        st.subheader(f"Just posted: entry #{e['no']}")
        left, right = st.columns([2, 3], gap="large")
        with left:
            html(journal_html([e]))
        with right:
            affected = [a for a, _, _ in e["key"]]
            cols = st.columns(len(affected))
            for col, acct in zip(cols, affected):
                with col:
                    html(t_account_html(acct, OPENING_FOR_T.get(acct, 0.0), by_acct.get(acct, []),
                                        new_id=e["entry_id"]))
        st.caption("The highlighted lines are the ones you just posted.")

    st.subheader("All T-accounts")
    show_idle = st.checkbox("Also show accounts with no activity yet", value=False)
    accts = [a for a in ac.ACCOUNTS if by_acct.get(a) or (show_idle and abs(OPENING_FOR_T.get(a, 0)) > 0.004)]
    if not accts:
        st.info("Post an entry to see the T-accounts.")
    else:
        cols = st.columns(3)
        for i, acct in enumerate(accts):
            with cols[i % 3]:
                html(t_account_html(acct, OPENING_FOR_T.get(acct, 0.0), by_acct.get(acct, []),
                                    new_id=ss.last_posted))
    st.caption("“Beg. bal.” is the account's balance on September 30, 2025, before any of your entries.")
    if ss.posted:
        st.button("Continue to step 3: trial balance", on_click=go, args=(PAGES[3],), type="primary")


OPENING_FOR_T = dict(OPENING)  # balance sheet accounts at 9/30/2025; revenue and expense accounts start at zero


# ===========================================================================
# PAGE: 3 · Trial balance
# ===========================================================================
def page_trial_balance():
    st.header("Step 3: Unadjusted trial balance")
    st.write("The trial balance lists every account's ending balance. If you posted correctly, "
             "total debits equal total credits.")
    if not ss.posted:
        st.info("You have not posted any entries yet, so this trial balance shows only the "
                "September 30 starting balances. Post entries in step 2 and watch it change.")
    rows = ac.trial_balance(OPENING, practice_activity())
    table, td, tc = trial_balance_html(rows)
    st.markdown(f"**As of December 31, 2025, after {len(ss.posted)} posted entries**")
    html(table)
    if abs(td - tc) < 0.005:
        st.success(f"Debits ({money(td)}) equal credits ({money(tc)}). The trial balance is in balance.")
    else:
        st.error(f"Debits ({money(td)}) and credits ({money(tc)}) differ by {money(abs(td - tc))}.")
    st.caption("Retained Earnings has a debit balance because the company has lost more money "
               "than it has earned since it started.")
    st.button("Continue to step 4: financial statements", on_click=go, args=(PAGES[4],), type="primary")


# ===========================================================================
# PAGE: 4 · Financial statements
# ===========================================================================
def page_statements():
    st.header("Step 4: Financial statements")
    if not ss.posted:
        st.info("No entries are posted yet, so nothing has changed from the starting balances. "
                "Post entries in step 2 and these statements update.")
    st.write(f"Based on your **{len(ss.posted)} posted entries** for October 1 to December 31, 2025.")

    activity = practice_activity()
    inc = ac.income_statement(activity)
    bs = ac.balance_sheet(OPENING, activity)

    left, right = st.columns(2, gap="large")
    with left:
        html(statement_html("Income statement", "For the quarter ended December 31, 2025 (your entries only)",
                            ["Amount"], income_rows(inc)))
        if inc["net_income"] < 0:
            st.caption("A net loss reduces retained earnings, and therefore owner's equity.")
    with right:
        rows, ok, a, le = balance_rows(bs)
        html(statement_html("Balance sheet", "Before and after your entries",
                            ["Sept 30, 2025", "Change", "Dec 31, 2025"], rows))
        if ok:
            st.success(f"Balanced: total assets {money(a)} equal total liabilities and equity {money(le)}.")
        else:
            st.error("The balance sheet does not balance.")
    st.info("How the statements connect: net income (loss) from the income statement flows into "
            "owner's equity on the balance sheet. Cash, inventory and accounts payable change "
            "because of the same entries you journalized.")


# ===========================================================================
# PAGE: Company-wide view
# ===========================================================================
def page_company():
    st.header("Company-wide view")
    st.write("These statements use **every sale and vendor invoice** in both data files "
             "(duplicate invoices removed), not just your practice set.")

    presets = {
        "Both years (2024–2025)": (dt.date(2024, 1, 1), dt.date(2025, 12, 31)),
        "2024": (dt.date(2024, 1, 1), dt.date(2024, 12, 31)),
        "2025": (dt.date(2025, 1, 1), dt.date(2025, 12, 31)),
        "Q4 2025 (the practice quarter)": (dt.date(2025, 10, 1), dt.date(2025, 12, 31)),
        "Choose my own dates": None,
    }
    choice = st.radio("Time period", list(presets), horizontal=True)
    if presets[choice] is None:
        picked = st.date_input("Start and end dates", value=(dt.date(2025, 1, 1), dt.date(2025, 12, 31)),
                               min_value=dt.date(2024, 1, 1), max_value=dt.date(2025, 12, 31))
        if not isinstance(picked, (tuple, list)) or len(picked) != 2:
            st.info("Choose both a start date and an end date.")
            return
        start, end = picked
    else:
        start, end = presets[choice]

    activity = ac.activity_between(LINES, start, end)
    opening = ac.balance_sheet_opening(LINES, start)
    inc = ac.income_statement(activity)
    bs = ac.balance_sheet(opening, activity)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Net sales", money(inc["net_sales"]))
    m2.metric("Gross profit", money(inc["gross_profit"]))
    m3.metric("Operating expenses", money(inc["total_expenses"]))
    m4.metric("Net income (loss)", f"-{money(-inc['net_income'])}" if inc["net_income"] < 0 else money(inc["net_income"]))
    m5.metric("Cash at end", money(bs["end"]["cash"]))

    if inc["net_income"] < 0:
        st.warning(f"The company lost {money(-inc['net_income'])} in this period. Vendor bills "
                   f"({money(inc['total_expenses'])}) were far larger than gross profit "
                   f"({money(inc['gross_profit'])}), so cash is shrinking and owner's equity is being used up.")

    left, right = st.columns(2, gap="large")
    with left:
        html(statement_html("Income statement", f"{start:%B %d, %Y} to {end:%B %d, %Y}",
                            ["Amount"], income_rows(inc)))
    with right:
        rows, ok, a, le = balance_rows(bs)
        begin_label = f"{(pd.Timestamp(start) - pd.Timedelta(days=1)):%b %d, %Y}"
        html(statement_html("Balance sheet", f"As of {end:%B %d, %Y}",
                            [begin_label, "Change", f"{end:%b %d, %Y}"], rows))
        if ok:
            st.success("Balanced: total assets equal total liabilities and owner's equity.")
        else:
            st.error("The balance sheet does not balance.")

    st.subheader("Month by month")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Net income (loss) each month**")
        st.bar_chart(MONTHLY["Net income (loss)"])
    with c2:
        st.markdown("**Cash at the end of each month**")
        st.line_chart(MONTHLY["Cash at month end"])

    st.subheader("Where your practice set fits")
    q4s = SALES[(SALES["sale_date"] >= ac.PRACTICE_START) & (SALES["sale_date"] <= ac.PRACTICE_END)]
    q4a = AP[(AP["invoice_date"] >= ac.PRACTICE_START) & (AP["invoice_date"] <= ac.PRACTICE_END)]
    ps = SALES[SALES["order_id"].isin(ac.PRACTICE_SALES)]
    pa = AP[AP["invoice_number"].isin(ac.PRACTICE_AP)]
    st.markdown(
        f"- **Retail sales in Q4 2025:** {len(q4s):,} sales with {money(q4s['net_sales'].sum())} in net sales. "
        f"Your practice set has {len(ps)} of them ({money(ps['net_sales'].sum())}).\n"
        f"- **Vendor invoices billed in Q4 2025:** {len(q4a):,} invoices totaling {money(q4a['invoice_amount'].sum())}. "
        f"Your practice set has {len(pa)} of them ({money(pa['invoice_amount'].sum())}).")
    st.caption(f"Starting balance sheet on January 1, 2024 (assumed): cash "
               f"{money(ac.OPENING_BALANCES['Cash'])}, inventory {money(ac.OPENING_BALANCES['Inventory'])}, "
               f"owner's capital {money(CAPITAL)}. {REMOVED} duplicate invoices were removed.")


# ---------------------------------------------------------------------------
# Show the chosen page
# ---------------------------------------------------------------------------
{
    PAGES[0]: page_start,
    PAGES[1]: page_journalize,
    PAGES[2]: page_post,
    PAGES[3]: page_trial_balance,
    PAGES[4]: page_statements,
    PAGES[5]: page_company,
}[page]()
