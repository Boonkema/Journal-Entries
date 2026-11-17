"""
Journal Entry Lab  (Streamlit app)  -  accounting-software style interface
-------------------------------------------------------------------------
Layout ideas borrowed from tools like QuickBooks Online and Xero:
  * a dark left navigation menu
  * a Home dashboard with summary cards and a "next step" prompt
  * a transactions list, and a journal entry form with live debit/credit totals
  * report-style income statement, balance sheet and trial balance with Export

All accounting logic is in accounting.py. This file only draws the screens.
"""

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st

import accounting as ac

st.set_page_config(page_title="Journal Entry Lab", page_icon="📒", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
COMPANY = ac.COMPANY_NAME
CAPITAL = -ac.OPENING_BALANCES["Owner's Capital"]

HOME, JOURNAL, LEDGER, COA = "Home", "Journal entries", "Ledger (T-accounts)", "Chart of accounts"
TB, INCOME, BALANCE, OVERVIEW = "Trial balance", "Income statement", "Balance sheet", "Company overview"
NAV = [
    (None, [(HOME, "🏠")]),
    ("ACCOUNTING", [(JOURNAL, "✏️"), (LEDGER, "📒"), (COA, "🗂️")]),
    ("REPORTS", [(TB, "⚖️"), (INCOME, "📈"), (BALANCE, "🏦")]),
    ("COMPANY", [(OVERVIEW, "🏢")]),
]

# ---------------------------------------------------------------------------
# Look and feel
# ---------------------------------------------------------------------------
CSS = """
<style>
:root {--green:#2CA01C; --green-d:#108000; --ink:#393A3D; --muted:#6B6C72; --line:#E4E5E7;
       --bg:#F4F5F8; --blue:#0077C5; --red:#D52B1E; --amber:#B26A00;}
.stApp {background: var(--bg); color: var(--ink);}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}
.block-container {padding-top: 1.6rem; max-width: 1280px;}
h1, h2, h3, h4, h5 {color: var(--ink);}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {background: #2C2F36; min-width: 260px;}
section[data-testid="stSidebar"] .block-container, section[data-testid="stSidebar"] > div {padding-top: 1rem;}
section[data-testid="stSidebar"] .stButton button {width: 100%; justify-content: flex-start; text-align: left;
    background: transparent; border: none; border-left: 3px solid transparent; border-radius: 0;
    padding: .5rem .9rem; box-shadow: none;}
section[data-testid="stSidebar"] .stButton button, section[data-testid="stSidebar"] .stButton button * {
    color: #E6E7E9 !important; font-weight: 500;}
section[data-testid="stSidebar"] .stButton button:hover {background: rgba(255,255,255,.08);}
section[data-testid="stSidebar"] .stButton button[kind="primary"],
section[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"] {
    background: rgba(44,160,28,.22); border-left: 3px solid var(--green);}
section[data-testid="stSidebar"] .stButton button[kind="primary"] *,
section[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"] * {color: #fff !important; font-weight: 700;}
.brand {display: flex; align-items: center; gap: 10px; padding: 4px 14px 2px;}
.brand .logo {background: var(--green); color: #fff; font-weight: 800; border-radius: 8px; width: 34px; height: 34px;
    display: flex; align-items: center; justify-content: center;}
.brand .name {color: #fff; font-weight: 700; font-size: 1.05rem;}
.co-line {color: #B8BAC0; font-size: .8rem; padding: 2px 14px 14px;}
.nav-h {color: #8E919A; font-size: .72rem; letter-spacing: .08em; font-weight: 700; padding: 14px 14px 4px;}
.side-prog {padding: 6px 14px;}
.side-prog .lbl {color: #D5D7DB; font-size: .78rem; display: flex; justify-content: space-between;}
.side-prog .bar {height: 6px; background: rgba(255,255,255,.15); border-radius: 3px; margin: 4px 0 8px; overflow: hidden;}
.side-prog .bar > div {height: 100%; background: var(--green);}

/* ---------- main-area buttons ---------- */
.stApp [data-testid="stMain"] .stButton button[kind="primary"],
.stApp [data-testid="stMain"] .stButton button[data-testid="stBaseButton-primary"] {
    background: var(--green); border-color: var(--green); color: #fff; font-weight: 600;}
.stApp [data-testid="stMain"] .stButton button[kind="primary"]:hover,
.stApp [data-testid="stMain"] .stButton button[data-testid="stBaseButton-primary"]:hover {
    background: var(--green-d); border-color: var(--green-d);}
div[data-testid="stVerticalBlockBorderWrapper"] {background: #fff; border-color: var(--line); border-radius: 8px;}

/* ---------- page header and stepper ---------- */
.pg-title {font-size: 1.7rem; font-weight: 800; color: var(--ink); line-height: 1.2;}
.pg-sub {color: var(--muted); margin: 2px 0 10px;}
.stepper {display: flex; background: #fff; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; margin: 8px 0 18px;}
.step {flex: 1; padding: 10px 14px; display: flex; align-items: center; gap: 10px; border-right: 1px solid var(--line); color: var(--muted);}
.step:last-child {border-right: none;}
.step .dot {width: 26px; height: 26px; border-radius: 50%; background: var(--line); color: var(--ink); display: flex;
    align-items: center; justify-content: center; font-weight: 700; font-size: .8rem; flex: none;}
.step.done .dot {background: var(--green); color: #fff;}
.step.active {background: #F0F9EE; color: var(--ink); font-weight: 700; box-shadow: inset 0 -3px 0 var(--green);}
.step .sub {display: block; font-size: .74rem; color: var(--muted); font-weight: 400;}

/* ---------- cards, chips, kpis ---------- */
.card {background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 16px 18px; color: var(--ink);
    box-shadow: 0 1px 2px rgba(0,0,0,.04); margin-bottom: 12px;}
.card h4 {margin: 0 0 8px; font-size: 1rem; color: var(--ink);}
.kpis {display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 14px;}
@media (max-width: 1000px) {.kpis {grid-template-columns: repeat(2, 1fr);} .stepper {flex-direction: column;}}
.kpi {background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; border-top: 4px solid var(--line);
    color: var(--ink);}
.kpi.green {border-top-color: var(--green);} .kpi.red {border-top-color: var(--red);} .kpi.blue {border-top-color: var(--blue);}
.kpi.amber {border-top-color: #FF8000;}
.kpi .k-l {color: var(--muted); font-size: .82rem; font-weight: 600;}
.kpi .k-v {font-size: 1.5rem; font-weight: 800; font-variant-numeric: tabular-nums;}
.kpi .k-s {color: var(--muted); font-size: .8rem;}
.chip {display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: .76rem; font-weight: 700;}
.chip.green {background: #E8F5E3; color: var(--green-d);} .chip.amber {background: #FFF1DC; color: var(--amber);}
.chip.gray {background: #ECEDEF; color: var(--muted);} .chip.red {background: #FDECEA; color: var(--red);}
.bar-row {display: flex; align-items: center; gap: 10px; margin: 6px 0; font-size: .85rem;}
.bar-row .b-l {width: 90px; color: var(--muted);} .bar-row .b-t {flex: 1; background: #ECEDEF; height: 14px; border-radius: 3px; overflow: hidden;}
.bar-row .b-f {height: 100%;} .bar-row .b-v {width: 110px; text-align: right; font-variant-numeric: tabular-nums;}
.seg {display: flex; height: 16px; border-radius: 4px; overflow: hidden; background: #ECEDEF; margin: 8px 0;}
.legend {display: flex; gap: 14px; flex-wrap: wrap; font-size: .82rem; color: var(--muted);}
.legend i {display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px;}
.nextcard {background: #F0F9EE; border: 1px solid #BFE3B8; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px; color: var(--ink);}
.nextcard .n-t {font-weight: 800; font-size: 1.05rem;} .nextcard .n-d {color: var(--muted);}

/* ---------- journal entry form ---------- */
.je-head {display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 6px; color: var(--ink);}
.je-no {font-weight: 800;} .je-lbl {color: var(--muted);} .je-date {color: var(--muted); font-size: .85rem; margin-left: 6px;}
.grid-h {font-size: .76rem; font-weight: 700; color: var(--muted); text-transform: none; border-bottom: 1px solid var(--line); padding-bottom: 2px;}
.rownum {color: var(--muted); font-size: .85rem; text-align: center;}
.je-totals {display: grid; grid-template-columns: 3.4fr 1.3fr 1.3fr; gap: 1rem; padding: 6px 0; font-weight: 700;
    border-top: 2px solid var(--ink); margin-top: 6px; font-variant-numeric: tabular-nums; color: var(--ink);}
.je-totals div:nth-child(2), .je-totals div:nth-child(3) {text-align: right; padding-right: 8px;}
.je-diff {font-size: .85rem; font-weight: 600; padding: 4px 10px; border-radius: 6px; margin-bottom: 8px; display: inline-block;}
.je-diff.ok {background: #E8F5E3; color: var(--green-d);} .je-diff.bad {background: #FDECEA; color: var(--red);}
.je-diff.idle {background: #ECEDEF; color: var(--muted);}

/* ---------- tables, reports, T-accounts ---------- */
.jtable, .ttable, .stmt table, .coa {width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; color: var(--ink);}
.jtable th, .ttable th, .coa th {text-align: left; font-weight: 700; font-size: .8rem; color: var(--muted); background: #F4F5F8;
    border-bottom: 1px solid var(--line); padding: 6px 8px;}
.jtable td, .ttable td, .coa td {padding: 5px 8px;}
.coa tr td {border-bottom: 1px solid var(--line);}
.jtable td.num, .ttable td.num, .jtable th.num, .ttable th.num {text-align: right;}
.jtable tr.firstline td {border-top: 1px solid var(--line);}
.jtable td.cr-acct {padding-left: 36px;}
.jtable td.memo {font-style: italic; color: var(--muted); padding-left: 36px; font-size: .85rem;}
.ttable tr.total td {border-top: 1px solid var(--ink); border-bottom: 3px double var(--ink); font-weight: 800;}
.report {background: #fff; border: 1px solid var(--line); border-radius: 8px; padding: 22px 28px; margin: 0 auto 14px;
    max-width: 880px; color: var(--ink); box-shadow: 0 1px 2px rgba(0,0,0,.04);}
.report .rp-co {text-align: center; font-weight: 800; font-size: 1.15rem;}
.report .rp-title {text-align: center; font-weight: 700; font-size: 1.05rem;}
.report .rp-period {text-align: center; color: var(--muted); font-size: .9rem;}
.report .rp-basis {text-align: center; color: var(--muted); font-size: .8rem; margin-bottom: 12px;}
.stmt th {text-align: right; font-size: .8rem; color: var(--muted); border-bottom: 1px solid var(--line); padding: 4px 8px;}
.stmt td {padding: 4px 8px;} .stmt td.num {text-align: right;}
.stmt tr.s-h td {font-weight: 800; padding-top: 12px;}
.stmt tr.s-i td:first-child {padding-left: 26px;}
.stmt tr.s-t td {border-top: 1px solid var(--ink); font-weight: 700;}
.stmt tr.s-g td {border-top: 1px solid var(--ink); border-bottom: 3px double var(--ink); font-weight: 800;}
.tacct {background: #fff; border: 1px solid #C9CBCF; border-radius: 6px; margin-bottom: 14px; overflow: hidden;
    font-variant-numeric: tabular-nums; color: var(--ink);}
.tacct .t-name {text-align: center; font-weight: 700; padding: 6px 8px; border-bottom: 2px solid var(--ink); background: #F4F5F8;}
.tacct .t-body {display: flex;}
.tacct .t-col {flex: 1; min-height: 58px; padding: 4px 8px;}
.tacct .t-col.dr {border-right: 2px solid var(--ink);}
.tacct .t-head {font-size: .74rem; color: var(--muted); padding-bottom: 2px;}
.tacct .trow {display: flex; justify-content: space-between; gap: 8px; font-size: .88rem; padding: 1px 3px; border-radius: 3px;}
.tacct .trow.new {background: #DFF3DA; font-weight: 700;}
.tacct .t-bal {border-top: 1px solid #C9CBCF; padding: 5px 10px; text-align: right; font-weight: 700; font-size: .9rem; background: #FAFAFB;}
.doc {background: #fff; border: 1px solid var(--line); border-left: 4px solid var(--blue); border-radius: 6px; padding: 14px 16px;
    margin-bottom: 12px; color: var(--ink);}
.doc .doc-tag {color: var(--blue); font-size: .75rem; font-weight: 800; letter-spacing: .05em;}
.doc .doc-title {font-weight: 800; font-size: 1.05rem; margin-bottom: 2px;}
.doc .doc-meta {color: var(--muted); font-size: .85rem; margin-bottom: 8px;}
.doc table {width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums;}
.doc td {padding: 3px 0;} .doc td.num {text-align: right;}
.doc tr.line-top td {border-top: 1px solid var(--line);} .doc tr.bold td {font-weight: 800;}
.doc .doc-note {margin-top: 8px; font-size: .85rem; color: var(--muted);}
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
    return f"-${abs(x):,.2f}" if x < -0.004 else f"${x:,.2f}"


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def show_table(df, **kwargs):
    """st.dataframe that stretches to full width on both old and new Streamlit versions."""
    try:
        return st.dataframe(df, width="stretch", **kwargs)
    except Exception:
        return st.dataframe(df, use_container_width=True, **kwargs)


def kpi_html(label, value, sub="", tone=""):
    return (f'<div class="kpi {tone}"><div class="k-l">{label}</div><div class="k-v">{value}</div>'
            f'<div class="k-s">{sub}</div></div>')


def statement_html(title, period, headers, rows):
    """Report with a centered header. rows = (label, [values] or None, style); style: h, i, t, g"""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for label, vals, style in rows:
        vals = vals if vals else [None] * len(headers)
        cells = "".join(f'<td class="num">{fmt(v) if v is not None else ""}</td>' for v in vals)
        body.append(f'<tr class="s-{style}"><td>{label}</td>{cells}</tr>')
    return (f'<div class="report"><div class="rp-co">{COMPANY}</div><div class="rp-title">{title}</div>'
            f'<div class="rp-period">{period}</div><div class="rp-basis">Accrual basis</div>'
            f'<div class="stmt"><table><thead><tr><th></th>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div></div>')


def rows_to_csv(headers, rows):
    out = []
    for label, vals, style in rows:
        rec = {"Line": label}
        for h, v in zip(headers, vals or [None] * len(headers)):
            rec[h] = None if v is None else round(v, 2)
        out.append(rec)
    return pd.DataFrame(out).to_csv(index=False).encode("utf-8")


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


def trial_balance_html(rows, period):
    body = "".join(f'<tr><td>{a}</td><td class="num">{fmt(d) if d else ""}</td>'
                   f'<td class="num">{fmt(c) if c else ""}</td></tr>' for a, d, c in rows)
    td = sum(r[1] for r in rows)
    tc = sum(r[2] for r in rows)
    body += f'<tr class="total"><td>TOTAL</td><td class="num">{fmt(td)}</td><td class="num">{fmt(tc)}</td></tr>'
    markup = (f'<div class="report"><div class="rp-co">{COMPANY}</div><div class="rp-title">Trial balance</div>'
              f'<div class="rp-period">{period}</div><div class="rp-basis">Accrual basis</div>'
              f'<table class="ttable"><thead><tr><th>Account</th><th class="num">Debit</th>'
              f'<th class="num">Credit</th></tr></thead><tbody>{body}</tbody></table></div>')
    return markup, td, tc


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
    return (f'<div class="doc"><div class="doc-tag">SOURCE DOCUMENT</div><div class="doc-title">Sales receipt</div>'
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
    return (f'<div class="doc"><div class="doc-tag">SOURCE DOCUMENT</div><div class="doc-title">Vendor invoice</div>'
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
ss.setdefault("page", HOME)
ss.setdefault("done", {})         # entry_id -> "correct" or "revealed"
ss.setdefault("posted", [])       # entry_ids in the order they were posted
ss.setdefault("attempts", {})     # entry_id -> number of tries
ss.setdefault("feedback", {})     # entry_id -> list of (level, message)
ss.setdefault("last_posted", None)
ss.setdefault("cur", {})          # "sale"/"ap" -> txn_id currently open
ss.setdefault("tblver", {"sale": 0, "ap": 0})


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


def clear_entry(entry_id):
    for i in range(4):
        st.session_state[f"acct_{entry_id}_{i}"] = ""
        st.session_state[f"dr_{entry_id}_{i}"] = None
        st.session_state[f"cr_{entry_id}_{i}"] = None
    st.session_state.feedback.pop(entry_id, None)


def txn_complete(t):
    return all(e["entry_id"] in ss.done for e in t["entries"])


def open_next(want, tid):
    group = [t for t in TXNS if t["type"] == want]
    ids = [t["txn_id"] for t in group]
    i = ids.index(tid)
    for k in range(1, len(ids) + 1):
        cand = group[(i + k) % len(ids)]
        if not txn_complete(cand):
            st.session_state.cur[want] = cand["txn_id"]
            st.session_state.tblver[want] += 1
            return


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
# Page furniture: sidebar, header, stepper
# ---------------------------------------------------------------------------
def sidebar():
    with st.sidebar:
        html('<div class="brand"><div class="logo">JE</div><div class="name">Journal Entry Lab</div></div>'
             f'<div class="co-line">{COMPANY} · Q4 2025</div>')
        for header, items in NAV:
            if header:
                html(f'<div class="nav-h">{header}</div>')
            for page, icon in items:
                st.button(f"{icon}  {page}", key=f"nav_{page}", on_click=go, args=(page,),
                          type="primary" if ss.page == page else "secondary")
        n_done, n_post = len(ss.done), len(ss.posted)
        html('<div class="nav-h">YOUR PROGRESS</div>'
             f'<div class="side-prog"><div class="lbl"><span>Journalized</span><span>{n_done}/{N_ENTRIES}</span></div>'
             f'<div class="bar"><div style="width:{100 * n_done / N_ENTRIES:.0f}%"></div></div>'
             f'<div class="lbl"><span>Posted</span><span>{n_post}/{N_ENTRIES}</span></div>'
             f'<div class="bar"><div style="width:{100 * n_post / N_ENTRIES:.0f}%"></div></div></div>')
        revealed = sum(1 for v in ss.done.values() if v == "revealed")
        if revealed:
            html(f'<div class="co-line">Answer key used on {revealed} entr{"y" if revealed == 1 else "ies"}.</div>')
        st.button("↺  Start over", key="nav_reset", on_click=reset_all)


def stepper_html(active):
    n_done, n_post = len(ss.done), len(ss.posted)
    steps = [
        ("Journalize", f"{n_done} of {N_ENTRIES} entries", n_done == N_ENTRIES),
        ("Post to ledger", f"{n_post} of {N_ENTRIES} posted", n_post == N_ENTRIES),
        ("Trial balance", "Debits = credits", n_post == N_ENTRIES),
        ("Statements", "Income and balance sheet", n_post == N_ENTRIES),
    ]
    out = []
    for i, (label, sub, done) in enumerate(steps, start=1):
        cls = "step" + (" done" if done else "") + (" active" if i == active else "")
        dot = "✓" if done else str(i)
        out.append(f'<div class="{cls}"><div class="dot">{dot}</div><div>{label}<span class="sub">{sub}</span></div></div>')
    return f'<div class="stepper">{"".join(out)}</div>'


def header(title, subtitle, step=None):
    html(f'<div class="pg-title">{title}</div><div class="pg-sub">{subtitle}</div>')
    if step:
        html(stepper_html(step))


# ===========================================================================
# HOME
# ===========================================================================
def next_action():
    n_done, n_post = len(ss.done), len(ss.posted)
    ready = n_done - n_post
    if n_done == 0:
        return ("Start with your first journal entry",
                "Open a transaction, read the source document, and record the debits and credits.",
                "Open journal entries", JOURNAL)
    if n_done < N_ENTRIES:
        return (f"Keep journalizing: {N_ENTRIES - n_done} entries to go",
                f"You have also journalized {ready} entr{'y' if ready == 1 else 'ies'} that "
                f"{'is' if ready == 1 else 'are'} not posted yet." if ready else
                "Pick the next transaction from your list.",
                "Open journal entries", JOURNAL)
    if n_post < N_ENTRIES:
        return (f"Post your entries: {N_ENTRIES - n_post} left",
                "Copy each journal entry into the T-accounts and watch the balances change.",
                "Open the ledger", LEDGER)
    return ("All entries are journalized and posted",
            "Check the trial balance, then read the income statement and balance sheet.",
            "Open the trial balance", TB)


def page_home():
    header("Home", f"{COMPANY} · Quarter ending December 31, 2025")
    title, desc, label, target = next_action()
    c1, c2 = st.columns([5, 1.6], vertical_alignment="center")
    with c1:
        html(f'<div class="nextcard"><div class="n-t">Next step: {title}</div><div class="n-d">{desc}</div></div>')
    with c2:
        st.button(label, on_click=go, args=(target,), type="primary", key="home_next")

    act = practice_activity()
    inc = ac.income_statement(act)
    cash = OPENING["Cash"] + act.get("Cash", 0.0)
    inv = OPENING["Inventory"] + act.get("Inventory", 0.0)
    ap_bal = -(OPENING["Accounts Payable"] + act.get("Accounts Payable", 0.0))
    ni = inc["net_income"]
    html('<div class="kpis">'
         + kpi_html("Cash", money(cash), f"{money(act.get('Cash', 0.0))} since Sept 30", "green")
         + kpi_html("Inventory", money(inv), f"{money(act.get('Inventory', 0.0))} since Sept 30", "blue")
         + kpi_html("Bills to pay (A/P)", money(ap_bal), f"{money(act.get('Accounts Payable', 0.0) * -1)} since Sept 30", "amber")
         + kpi_html("Net income (loss), your entries", money(ni), "Practice entries posted so far",
                    "red" if ni < 0 else "green")
         + '</div>')

    left, right = st.columns(2, gap="medium")
    with left:
        income = inc["net_sales"]
        spend = inc["cogs"] + inc["total_expenses"]
        top = max(income, spend, 1)
        html('<div class="card"><h4>Profit and loss · your posted entries</h4>'
             f'<div class="bar-row"><span class="b-l">Net sales</span><span class="b-t"><span class="b-f" '
             f'style="display:block;width:{100 * income / top:.0f}%;background:#2CA01C"></span></span>'
             f'<span class="b-v">{money(income)}</span></div>'
             f'<div class="bar-row"><span class="b-l">Costs and expenses</span><span class="b-t"><span class="b-f" '
             f'style="display:block;width:{100 * spend / top:.0f}%;background:#D52B1E"></span></span>'
             f'<span class="b-v">{money(spend)}</span></div>'
             f'<div class="bar-row"><span class="b-l"><b>Net income (loss)</b></span><span class="b-t" style="background:none"></span>'
             f'<span class="b-v"><b>{money(ni)}</b></span></div></div>')
    with right:
        bills = [t for t in TXNS if t["type"] == "ap"]
        paid_amt = sum(t["source"]["invoice_amount"] for t in bills if t["paid"])
        od_amt = sum(t["source"]["invoice_amount"] for t in bills if not t["paid"] and t["source"]["status"] == "Overdue")
        open_amt = sum(t["source"]["invoice_amount"] for t in bills if not t["paid"] and t["source"]["status"] != "Overdue")
        tot = max(paid_amt + od_amt + open_amt, 1)
        html('<div class="card"><h4>Vendor bills in your practice set</h4>'
             f'<div class="seg"><div style="width:{100 * od_amt / tot:.1f}%;background:#D52B1E"></div>'
             f'<div style="width:{100 * open_amt / tot:.1f}%;background:#FF8000"></div>'
             f'<div style="width:{100 * paid_amt / tot:.1f}%;background:#2CA01C"></div></div>'
             f'<div class="legend"><span><i style="background:#D52B1E"></i>Overdue {money(od_amt)}</span>'
             f'<span><i style="background:#FF8000"></i>Open {money(open_amt)}</span>'
             f'<span><i style="background:#2CA01C"></i>Paid {money(paid_amt)}</span></div>'
             '<div class="doc-note" style="margin-top:8px;color:#6B6C72;font-size:.85rem">'
             'Overdue and open bills stay in Accounts Payable on the balance sheet.</div></div>')

    st.subheader("How this works")
    g1, g2, g3, g4 = st.columns(4, gap="small")
    for col, (n, t, d) in zip([g1, g2, g3, g4], [
        ("1", "Journalize", "Read a receipt or invoice and record the entry. The answer key checks you right away."),
        ("2", "Post", "Copy each entry into T-accounts and watch balances move."),
        ("3", "Trial balance", "Confirm total debits equal total credits."),
        ("4", "Statements", "See the income statement and balance sheet change."),
    ]):
        with col:
            html(f'<div class="card"><h4>{n} · {t}</h4><div style="color:#6B6C72;font-size:.9rem">{d}</div></div>')

    with st.expander("Assumptions behind this company"):
        st.markdown(
            "- The data files only contain transactions, so the company's **starting balance sheet on "
            f"January 1, 2024 is assumed**: cash {money(ac.OPENING_BALANCES['Cash'])}, inventory "
            f"{money(ac.OPENING_BALANCES['Inventory'])}, and owner's capital {money(CAPITAL)}.\n"
            "- Every payment method (cash, cards, digital wallets, ACH, checks) is treated as **cash**.\n"
            "- The company never buys inventory in this data, so inventory only goes down.\n"
            "- An expense is recorded when the vendor bill is dated, not when it is paid.\n"
            "- A payment dated after December 31, 2025 is not recorded, so that bill stays in Accounts Payable.\n"
            f"- **{REMOVED} duplicate vendor invoices** (the same invoice number billed twice) were removed "
            "before anything was calculated.\n"
            "- Your practice quarter starts with the company's balances as of September 30, 2025, "
            "calculated from all earlier transactions.")


# ===========================================================================
# JOURNAL ENTRIES
# ===========================================================================
def entry_card(e):
    eid = e["entry_id"]
    status = ss.done.get(eid)
    chip = ('<span class="chip green">Saved</span>' if status == "correct"
            else '<span class="chip amber">Answer shown</span>' if status
            else '<span class="chip gray">Not saved</span>')
    html(f'<div class="je-head"><div><span class="je-no">Journal entry #{e["no"]}</span>'
         f'<span class="je-lbl"> · {e["label"]}</span></div>'
         f'<div>{chip}<span class="je-date">Journal date {e["date"]:%m/%d/%Y}</span></div></div>')

    if status:
        html(journal_html([e]))
        return

    widths = [0.4, 3, 1.3, 1.3]
    h0, h1, h2, h3 = st.columns(widths)
    h0.markdown('<div class="grid-h">#</div>', unsafe_allow_html=True)
    h1.markdown('<div class="grid-h">Account</div>', unsafe_allow_html=True)
    h2.markdown('<div class="grid-h">Debits</div>', unsafe_allow_html=True)
    h3.markdown('<div class="grid-h">Credits</div>', unsafe_allow_html=True)

    options = [""] + ac.JOURNAL_ACCOUNTS
    rows = []
    for i in range(4):
        c0, c1, c2, c3 = st.columns(widths, vertical_alignment="center")
        c0.markdown(f'<div class="rownum">{i + 1}</div>', unsafe_allow_html=True)
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

    tot_dr = round(sum((d or 0) for _, d, _ in rows), 2)
    tot_cr = round(sum((c or 0) for _, _, c in rows), 2)
    if tot_dr == 0 and tot_cr == 0:
        diff_html = '<span class="je-diff idle">Enter debits first, then credits</span>'
    elif abs(tot_dr - tot_cr) < 0.005:
        diff_html = '<span class="je-diff ok">Balanced</span>'
    else:
        diff_html = f'<span class="je-diff bad">Out of balance by {money(abs(tot_dr - tot_cr))}</span>'
    html(f'<div class="je-totals"><div>Total</div><div>{fmt(tot_dr) if tot_dr else "0.00"}</div>'
         f'<div>{fmt(tot_cr) if tot_cr else "0.00"}</div></div>{diff_html}')

    b1, b2, _ = st.columns([1.2, 1, 3])
    save = b1.button("Save entry", key=f"save_{eid}", type="primary")
    b2.button("Clear", key=f"clear_{eid}", on_click=clear_entry, args=(eid,))

    if save:
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


def txn_table(group):
    recs = []
    for t in group:
        r = t["source"]
        n_done = sum(1 for e in t["entries"] if e["entry_id"] in ss.done)
        status = "✅ Done" if n_done == len(t["entries"]) else ("🟡 In progress" if n_done else "⬜ To do")
        if t["type"] == "sale":
            desc = f"{r['product']} ×{int(r['quantity'])}" + (f" · {r['discount_pct']:.0f}% off" if r["discount_pct"] > 0 else "")
            num, amount = r["order_id"], float(r["net_sales"])
        else:
            desc = r["vendor_name"]
            num, amount = r["invoice_number"], float(r["invoice_amount"])
        recs.append({"Status": status, "Date": t["date"].strftime("%m/%d/%Y"), "No.": num,
                     "Description": desc, "Amount": amount, "Entries saved": f"{n_done} of {len(t['entries'])}"})
    return pd.DataFrame(recs)


def page_journal():
    header("Journal entries", "Open a transaction from the list, then record its journal entries.", step=1)

    kind = st.radio("Transactions", ["Retail sales", "Vendor bills"], horizontal=True)
    want = "sale" if kind == "Retail sales" else "ap"
    group = [t for t in TXNS if t["type"] == want]
    if want not in ss.cur:
        first_open = next((t for t in group if not txn_complete(t)), group[0])
        ss.cur[want] = first_open["txn_id"]

    event = show_table(
        txn_table(group), hide_index=True, height=390, key=f"tbl_{want}_{ss.tblver[want]}",
        on_select="rerun", selection_mode="single-row",
        column_config={"Amount": st.column_config.NumberColumn(format="$%.2f")})
    selection = getattr(event, "selection", None)
    rows_sel = list(selection.rows) if selection is not None else []
    prev = ss.get(f"prevsel_{want}")
    if rows_sel and rows_sel != prev:
        ss.cur[want] = group[rows_sel[0]]["txn_id"]
    ss[f"prevsel_{want}"] = rows_sel
    st.caption("Click a row to open it.")

    t = next(x for x in group if x["txn_id"] == ss.cur[want])
    html(f'<div class="pg-title" style="font-size:1.25rem;margin-top:6px">{t["title"]}</div>'
         f'<div class="pg-sub">{len(t["entries"])} journal {"entry" if len(t["entries"]) == 1 else "entries"} to record</div>')

    left, right = st.columns([2, 3], gap="large")
    with left:
        html(sale_doc_html(t["source"]) if t["type"] == "sale" else invoice_doc_html(t))
        if t["type"] == "ap" and not t["paid"]:
            st.caption("This invoice has no payment, so there is only one entry to record.")
    with right:
        for e in t["entries"]:
            with st.container(border=True):
                entry_card(e)
        if txn_complete(t):
            st.info("💡 " + t["takeaway"])
            if any(not txn_complete(x) for x in group):
                st.button("Open next unfinished transaction", on_click=open_next, args=(want, t["txn_id"]),
                          type="primary", key=f"next_{t['txn_id']}")

    st.divider()
    n_ready = len([e for e in ENTRIES if e["entry_id"] in ss.done and e["entry_id"] not in ss.posted])
    c1, c2 = st.columns([3, 2], vertical_alignment="center")
    with c1:
        with st.expander(f"General journal so far ({len(ss.done)} entries)"):
            done_entries = [e for e in ENTRIES if e["entry_id"] in ss.done]
            if done_entries:
                html(journal_html(done_entries))
            else:
                st.write("Entries you save correctly will appear here.")
    with c2:
        if n_ready:
            st.button(f"Next: post {n_ready} entr{'y' if n_ready == 1 else 'ies'} to the ledger",
                      on_click=go, args=(LEDGER,), type="primary", key="to_ledger")


# ===========================================================================
# LEDGER (T-accounts)
# ===========================================================================
OPENING_FOR_T = dict(OPENING)  # balance sheet accounts at 9/30/2025; revenue and expense accounts start at zero


def ledger_lines():
    by_acct = {}
    for eid in ss.posted:
        e = ENTRY_BY_ID[eid]
        for acct, side, amt in e["key"]:
            by_acct.setdefault(acct, []).append({"no": e["no"], "side": side, "amount": amt, "entry_id": eid})
    return by_acct


def page_ledger():
    header("Ledger (T-accounts)",
           "Posting copies each line of a journal entry into its T-account: debits on the left, credits on the right.",
           step=2)
    ready = [e for e in ENTRIES if e["entry_id"] in ss.done and e["entry_id"] not in ss.posted]
    if not ss.done:
        st.info("Save at least one journal entry first, then come back to post it.")
        st.button("Go to journal entries", on_click=go, args=(JOURNAL,), type="primary", key="ledger_go")
        return

    with st.container(border=True):
        if ready:
            c1, c2, c3 = st.columns([4, 1.5, 1.8], vertical_alignment="bottom")
            pick = c1.selectbox(
                f"Ready to post ({len(ready)})", [e["entry_id"] for e in ready], key="post_pick",
                format_func=lambda i: f"#{ENTRY_BY_ID[i]['no']} · {ENTRY_BY_ID[i]['date']:%m/%d} · "
                                      f"{ENTRY_BY_ID[i]['memo']}")
            c2.button("Post this entry", on_click=post_entry, args=(pick,), type="primary", key="post_one")
            c3.button(f"Post all {len(ready)}", on_click=post_all,
                      args=([e["entry_id"] for e in ready],), key="post_all")
        elif len(ss.posted) < N_ENTRIES:
            st.success("Everything you have saved is posted. Journalize more entries to keep going.")
        else:
            st.success("All entries are posted.")

    by_acct = ledger_lines()
    if ss.last_posted and ss.last_posted in ss.posted:
        e = ENTRY_BY_ID[ss.last_posted]
        st.subheader(f"Just posted: entry #{e['no']}")
        left, right = st.columns([2, 3], gap="large")
        with left:
            html(f'<div class="card">{journal_html([e])}</div>')
        with right:
            affected = [a for a, _, _ in e["key"]]
            for col, acct in zip(st.columns(len(affected)), affected):
                with col:
                    html(t_account_html(acct, OPENING_FOR_T.get(acct, 0.0), by_acct.get(acct, []), new_id=e["entry_id"]))
        st.caption("Highlighted lines are the ones you just posted.")

    st.subheader("All T-accounts")
    show_idle = st.checkbox("Also show accounts with no activity yet", value=False)
    accts = [a for a in ac.ACCOUNTS if by_acct.get(a) or (show_idle and abs(OPENING_FOR_T.get(a, 0)) > 0.004)]
    if not accts:
        st.info("Post an entry to see the T-accounts.")
    else:
        cols = st.columns(3)
        for i, acct in enumerate(accts):
            with cols[i % 3]:
                html(t_account_html(acct, OPENING_FOR_T.get(acct, 0.0), by_acct.get(acct, []), new_id=ss.last_posted))
    st.caption("“Beg. bal.” is the account's balance on September 30, 2025, before any of your entries.")
    if ss.posted:
        st.button("Next: trial balance", on_click=go, args=(TB,), type="primary", key="to_tb")


# ===========================================================================
# CHART OF ACCOUNTS
# ===========================================================================
def page_coa():
    header("Chart of accounts", "Every account the company uses, with its type and current balance.")
    act = practice_activity()
    rows = []
    for name, (typ, side) in ac.ACCOUNTS.items():
        bal = OPENING.get(name, 0.0) + act.get(name, 0.0)
        shown = f"{abs(bal):,.2f} {'Dr' if bal > 0 else 'Cr'}" if abs(bal) > 0.004 else "–"
        rows.append(f"<tr><td>{name}</td><td>{typ}</td><td>{side}</td><td class='num' style='text-align:right'>{shown}</td></tr>")
    html('<div class="card"><table class="coa"><thead><tr><th>Account</th><th>Type</th><th>Normal balance</th>'
         '<th style="text-align:right">Balance now</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>')
    st.caption("Balance now = September 30, 2025 balance plus the entries you have posted.")
    html('<div class="card"><h4>Debit and credit rules</h4><div style="line-height:1.7">'
         '<b>Assets</b> and <b>expenses</b> go up with a debit and down with a credit.<br>'
         '<b>Liabilities</b>, <b>equity</b> and <b>revenue</b> go up with a credit and down with a debit.<br>'
         '<b>Sales Discounts</b> is a contra-revenue account: it works like an expense (debit to increase).<br>'
         'Total debits must always equal total credits.</div></div>')


# ===========================================================================
# REPORTS
# ===========================================================================
PRACTICE_PERIOD = "As of December 31, 2025 (your posted entries only)"


def posted_banner():
    if not ss.posted:
        st.info("You have not posted any entries yet, so this report shows only the September 30 starting balances. "
                "Post entries in the ledger and it updates.")
    else:
        st.caption(f"Based on your {len(ss.posted)} posted entries.")


def page_trial_balance():
    header("Trial balance", "Every account's ending balance. If you posted correctly, debits equal credits.", step=3)
    posted_banner()
    rows = ac.trial_balance(OPENING, practice_activity())
    markup, td, tc = trial_balance_html(rows, PRACTICE_PERIOD)
    html(markup)
    if abs(td - tc) < 0.005:
        st.success(f"Debits ({money(td)}) equal credits ({money(tc)}). The trial balance is in balance.")
    else:
        st.error(f"Debits ({money(td)}) and credits ({money(tc)}) differ by {money(abs(td - tc))}.")
    st.caption("Retained Earnings has a debit balance because the company has lost more money than it has earned.")
    csv = pd.DataFrame(rows, columns=["Account", "Debit", "Credit"]).to_csv(index=False).encode("utf-8")
    c1, c2, _ = st.columns([1.3, 2, 3])
    c1.download_button("Export to CSV", csv, "trial_balance.csv", "text/csv", key="dl_tb")
    c2.button("Next: income statement", on_click=go, args=(INCOME,), type="primary", key="to_is")


def page_income():
    header("Income statement", "Revenue minus costs and expenses for the quarter, from your posted entries.", step=4)
    posted_banner()
    inc = ac.income_statement(practice_activity())
    html('<div class="kpis">'
         + kpi_html("Net sales", money(inc["net_sales"]), "After discounts", "green")
         + kpi_html("Gross profit", money(inc["gross_profit"]), "Net sales minus cost of goods sold", "blue")
         + kpi_html("Operating expenses", money(inc["total_expenses"]), "Vendor bills", "amber")
         + kpi_html("Net income (loss)", money(inc["net_income"]), "Gross profit minus expenses",
                    "red" if inc["net_income"] < 0 else "green") + '</div>')
    rows = income_rows(inc)
    html(statement_html("Income statement", "For the quarter ended December 31, 2025 (your entries only)", ["Amount"], rows))
    c1, c2, _ = st.columns([1.3, 2, 3])
    c1.download_button("Export to CSV", rows_to_csv(["Amount"], rows), "income_statement.csv", "text/csv", key="dl_is")
    c2.button("Next: balance sheet", on_click=go, args=(BALANCE,), type="primary", key="to_bs")
    st.info("Net income (loss) flows into owner's equity on the balance sheet.")


def page_balance():
    header("Balance sheet", "What the company owns, owes, and the owners' stake, before and after your entries.", step=4)
    posted_banner()
    bs = ac.balance_sheet(OPENING, practice_activity())
    rows, ok, a, le = balance_rows(bs)
    html(statement_html("Balance sheet", "Before and after your entries",
                        ["Sept 30, 2025", "Change", "Dec 31, 2025"], rows))
    if ok:
        st.success(f"Balanced: total assets {money(a)} equal total liabilities and owner's equity {money(le)}.")
    else:
        st.error("The balance sheet does not balance.")
    st.download_button("Export to CSV", rows_to_csv(["Sept 30, 2025", "Change", "Dec 31, 2025"], rows),
                       "balance_sheet.csv", "text/csv", key="dl_bs")


# ===========================================================================
# COMPANY OVERVIEW (all records)
# ===========================================================================
def page_overview():
    header("Company overview", "Statements built from every sale and vendor invoice in both data files "
                               "(duplicate invoices removed), not just your practice set.")
    presets = {
        "Both years": (dt.date(2024, 1, 1), dt.date(2025, 12, 31)),
        "2024": (dt.date(2024, 1, 1), dt.date(2024, 12, 31)),
        "2025": (dt.date(2025, 1, 1), dt.date(2025, 12, 31)),
        "Q4 2025": (dt.date(2025, 10, 1), dt.date(2025, 12, 31)),
        "Custom dates": None,
    }
    choice = st.radio("Period", list(presets), horizontal=True)
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

    html('<div class="kpis">'
         + kpi_html("Net sales", money(inc["net_sales"]), f"{start:%b %d, %Y} to {end:%b %d, %Y}", "green")
         + kpi_html("Gross profit", money(inc["gross_profit"]), "After cost of goods sold", "blue")
         + kpi_html("Operating expenses", money(inc["total_expenses"]), "Vendor bills", "amber")
         + kpi_html("Net income (loss)", money(inc["net_income"]), f"Cash at end: {money(bs['end']['cash'])}",
                    "red" if inc["net_income"] < 0 else "green") + '</div>')
    if inc["net_income"] < 0:
        st.warning(f"The company lost {money(-inc['net_income'])} in this period. Vendor bills "
                   f"({money(inc['total_expenses'])}) were far larger than gross profit "
                   f"({money(inc['gross_profit'])}), so cash is shrinking and owner's equity is being used up.")

    tab_is, tab_bs, tab_ch = st.tabs(["Income statement", "Balance sheet", "Month by month"])
    with tab_is:
        rows = income_rows(inc)
        html(statement_html("Income statement", f"{start:%B %d, %Y} to {end:%B %d, %Y}", ["Amount"], rows))
        st.download_button("Export to CSV", rows_to_csv(["Amount"], rows), "company_income_statement.csv",
                           "text/csv", key="dl_co_is")
    with tab_bs:
        rows, ok, a, le = balance_rows(bs)
        begin_label = f"{(pd.Timestamp(start) - pd.Timedelta(days=1)):%b %d, %Y}"
        heads = [begin_label, "Change", f"{end:%b %d, %Y}"]
        html(statement_html("Balance sheet", f"As of {end:%B %d, %Y}", heads, rows))
        if ok:
            st.success("Balanced: total assets equal total liabilities and owner's equity.")
        else:
            st.error("The balance sheet does not balance.")
        st.download_button("Export to CSV", rows_to_csv(heads, rows), "company_balance_sheet.csv",
                           "text/csv", key="dl_co_bs")
    with tab_ch:
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
    st.caption(f"Starting balance sheet on January 1, 2024 (assumed): cash {money(ac.OPENING_BALANCES['Cash'])}, "
               f"inventory {money(ac.OPENING_BALANCES['Inventory'])}, owner's capital {money(CAPITAL)}. "
               f"{REMOVED} duplicate invoices were removed.")


# ---------------------------------------------------------------------------
# Draw the page
# ---------------------------------------------------------------------------
html(CSS)
sidebar()
{
    HOME: page_home,
    JOURNAL: page_journal,
    LEDGER: page_ledger,
    COA: page_coa,
    TB: page_trial_balance,
    INCOME: page_income,
    BALANCE: page_balance,
    OVERVIEW: page_overview,
}[ss.page]()
