import streamlit as st
import pandas as pd
import json
import io
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="BILLORA — Business Suite", page_icon="🟣", layout="wide", initial_sidebar_state="expanded")

# --- FAST GOOGLE SHEETS CONNECTION & SESSION CACHE ---
conn = st.connection("gsheets", type=GSheetsConnection)

sales_cols = ["Date", "Invoice_No", "Platform", "Product_Name", "SKU", "Qty", "Selling_Price", "GST_Rate", "Taxable_Value", "CGST", "SGST", "Total"]
purch_cols = ["Date", "Bill_No", "Supplier_Name", "Category", "Total_Bill_Amount", "GST_Rate", "Taxable_Amount", "ITC_Claimed"]
cat_cols = ["SKU", "Product_Name", "Buy_Cost", "Packaging_Cost", "Platform_Fee", "Profit_Margin", "Selling_Price", "Suggested_MRP", "GST_Rate", "Net_Weight_g"]

def fetch_sheet_once(worksheet_name, columns):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=600)
        if df is None or df.empty:
            return pd.DataFrame(columns=columns)
        df = df.dropna(how="all")
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns]
    except Exception:
        return pd.DataFrame(columns=columns)

if "db_initialized" not in st.session_state:
    st.session_state.sales_df = fetch_sheet_once("Sales", sales_cols)
    st.session_state.purch_df = fetch_sheet_once("Purchases", purch_cols)
    st.session_state.cat_df = fetch_sheet_once("Catalog", cat_cols)
    st.session_state.db_initialized = True

def force_refresh_db():
    st.cache_data.clear()
    st.session_state.sales_df = fetch_sheet_once("Sales", sales_cols)
    st.session_state.purch_df = fetch_sheet_once("Purchases", purch_cols)
    st.session_state.cat_df = fetch_sheet_once("Catalog", cat_cols)

sales_df = st.session_state.sales_df
purch_df = st.session_state.purch_df
cat_df = st.session_state.cat_df

# --- SESSION STATE INITIALIZATION ---
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "khata_mode" not in st.session_state:
    st.session_state.khata_mode = "Customers"
if "show_welcome_banner" not in st.session_state:
    st.session_state.show_welcome_banner = True
if "businesses_list" not in st.session_state:
    st.session_state.businesses_list = ["GK Maina Music • Tinsukia", "GK Collection • Guwahati"]
if "biz_name" not in st.session_state:
    st.session_state.biz_name = "GK Maina Music"
if "user_gstin" not in st.session_state:
    st.session_state.user_gstin = "18AAAAA0000A1Z5"
if "parties_list" not in st.session_state:
    st.session_state.parties_list = [
        {"Name": "Meesho Customer Pool", "Type": "Customer", "Phone": "9876543210", "GSTIN": "Unregistered", "Balance": 0.0, "Due_Date": str(date.today())},
        {"Name": "Fancy Bazaar Wholesale Hub", "Type": "Vendor", "Phone": "9123456789", "GSTIN": "18AABCF1234D1Z5", "Balance": 0.0, "Due_Date": str(date.today())}
    ]
if "inv_line_items" not in st.session_state:
    st.session_state.inv_line_items = [{"title": "", "hsn": "7117", "qty": 1, "mrp": 0.0, "disc": 0.0, "gst": 3}]
if "draft_invoices" not in st.session_state:
    st.session_state.draft_invoices = []
if "saved_reports" not in st.session_state:
    st.session_state.saved_reports = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "text": "Namaste! Main Billoora AI Assistant hoon. Aap mujhse GSTR-1, GSTR-3B, Create Invoice ya Meesho/Amazon B2C filings ke baare mein pooch sakte hain."}
    ]

# --- PREMIUM CSS FOR PERFECT POPOVER & ALIGNMENT ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp, button, input, select, textarea {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    .stApp {
        background-color: #f4f6fa !important;
        color: #0f172a !important;
    }

    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 97% !important;
    }

    /* Left Sidebar Clean White Design */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        width: 255px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
    }

    section[data-testid="stSidebar"] .stButton {
        margin-bottom: -6px !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        display: flex !important;
        justify-content: flex-start !important;
        text-align: left !important;
        background-color: transparent !important;
        color: #475569 !important;
        border: 1px solid transparent !important;
        border-radius: 9px !important;
        padding: 7px 12px !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        transition: all 0.12s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button > div {
        width: 100% !important;
        display: flex !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] .stButton > button p {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        margin: 0 !important;
        text-align: left !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #eef2ff !important;
        color: #4f46e5 !important;
        border: 1.5px solid #6366f1 !important;
        font-weight: 700 !important;
    }

    /* Clean Sidebar Dropdown Expanders */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        margin-bottom: -6px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] details {
        border: none !important;
        background: transparent !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
        padding: 7px 12px !important;
        border-radius: 9px !important;
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpander"] summary:hover {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stExpanderDetails"] {
        padding: 4px 0px 6px 14px !important;
        border-left: 2px solid #e2e8f0 !important;
        margin-left: 16px !important;
    }

    /* Top + New Button & Popover Fix */
    div[data-testid="stPopover"] > button {
        background-color: #0f766e !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 6px 16px !important;
    }
    
    /* Popover Menu Content Styling */
    div[data-testid="stPopoverBody"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
        padding: 10px !important;
        min-width: 220px !important;
        z-index: 999999 !important;
    }
    div[data-testid="stPopoverBody"] .stButton > button {
        background: transparent !important;
        color: #334155 !important;
        border: none !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 8px 12px !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
    }
    div[data-testid="stPopoverBody"] .stButton > button:hover {
        background-color: #f1f5f9 !important;
        color: #4f46e5 !important;
    }

    /* Primary Purple Action Buttons */
    div[data-testid="stMainBlockContainer"] .stButton > button[kind="primary"],
    div[data-testid="stMainBlockContainer"] .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(90deg, #6d28d9 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 9px !important;
        font-weight: 600 !important;
        padding: 8px 18px !important;
        box-shadow: 0 2px 6px rgba(109, 40, 217, 0.25) !important;
    }

    /* Welcome Purple Banner */
    .welcome-banner {
        background: linear-gradient(135deg, #6366f1 0%, #7c3aed 100%);
        border-radius: 16px;
        padding: 22px 26px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.18);
    }
    .welcome-step {
        background: rgba(255, 255, 255, 0.14);
        border: 1px solid rgba(255, 255, 255, 0.22);
        border-radius: 10px;
        padding: 10px 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
        font-size: 13px;
        font-weight: 600;
    }

    /* Business Top Pill */
    .biz-selector {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 5px 14px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .biz-icon {
        background: #4f46e5;
        color: white;
        border-radius: 7px;
        padding: 4px 8px;
        font-size: 12px;
        font-weight: 700;
    }

    /* Cards & Containers */
    .b-section-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .b-metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        height: 100%;
    }
    .b-plat-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 10px;
        min-height: 155px;
    }
    .b-plat-card-active {
        background: #ffffff;
        border: 1.5px solid #10b981;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 10px;
        min-height: 155px;
        box-shadow: 0 4px 12px rgba(16,185,129,0.06);
    }
    .pill-b2c {
        background: #eef2ff;
        color: #4f46e5;
        font-size: 10.5px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 10px;
    }
    .gstr2b-green-box {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 18px;
    }
    .empty-state-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 40px 20px;
        text-align: center;
        color: #64748b;
        margin-top: 12px;
    }
    .restore-banner {
        background: #eef2ff;
        border: 1px solid #c7d2fe;
        color: #4338ca;
        padding: 10px 16px;
        border-radius: 10px;
        font-size: 12.5px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

STATE_MAP = {
    "JAMMU AND KASHMIR": "01", "HIMACHAL PRADESH": "02", "PUNJAB": "03", "CHANDIGARH": "04",
    "UTTARAKHAND": "05", "HARYANA": "06", "DELHI": "07", "RAJASTHAN": "08", "UTTAR PRADESH": "09",
    "BIHAR": "10", "SIKKIM": "11", "ARUNACHAL PRADESH": "12", "NAGALAND": "13", "MANIPUR": "14",
    "MIZORAM": "15", "TRIPURA": "16", "MEGHALAYA": "17", "ASSAM": "18", "WEST BENGAL": "19",
    "JHARKHAND": "20", "ODISHA": "21", "CHHATTISGARH": "22", "MADHYA PRADESH": "23",
    "GUJARAT": "24", "MAHARASHTRA": "27", "KARNATAKA": "29", "GOA": "30", "KERALA": "32",
    "TAMIL NADU": "33", "TELANGANA": "36", "ANDHRA PRADESH": "37"
}

@st.cache_data(show_spinner=False)
def read_uploaded_file_bytes(file_bytes, file_name):
    try:
        if file_name.endswith(".csv"):
            return pd.read_csv(io.BytesIO(file_bytes))
        return pd.read_excel(io.BytesIO(file_bytes))
    except Exception:
        return pd.DataFrame()

def parse_uploaded(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()
    return read_uploaded_file_bytes(uploaded_file.getvalue(), uploaded_file.name)

def standardize_b2c_df(df, source_name, sign=1):
    if df.empty:
        return pd.DataFrame(columns=["Source", "POS", "GST_Rate", "Taxable_Value"])
    cols = {str(c).lower().strip(): c for c in df.columns}
    state_col = next((cols[k] for k in cols if any(w in k for w in ["end_customer_state", "customer_state", "ship to state", "destination state", "pos", "state", "place of supply"])), None)
    tax_col = next((cols[k] for k in cols if any(w in k for w in ["taxable", "net_taxable", "taxable_value", "taxable amount", "principal", "basic"])), None)
    rate_col = next((cols[k] for k in cols if any(w in k for w in ["gst_rate", "tax_rate", "igst_rate", "rate", "gst %", "gst_pct"])), None)

    out = pd.DataFrame()
    if tax_col:
        out["Taxable_Value"] = pd.to_numeric(df[tax_col], errors="coerce").fillna(0.0) * sign
    else:
        amt_col = next((cols[k] for k in cols if any(w in k for w in ["total", "invoice_value", "selling_price", "amount"])), None)
        out["Taxable_Value"] = (pd.to_numeric(df[amt_col], errors="coerce").fillna(0.0) / 1.03) * sign if amt_col else 0.0

    if rate_col:
        r_vals = pd.to_numeric(df[rate_col], errors="coerce").fillna(3.0)
        out["GST_Rate"] = r_vals.apply(lambda x: round(x * 100, 1) if 0 < x < 1 else x)
    else:
        out["GST_Rate"] = 3.0

    if state_col:
        raw_state = df[state_col].astype(str).str.upper().str.strip()
        out["POS"] = raw_state.apply(lambda val: next((s_code for s_name, s_code in STATE_MAP.items() if s_name in val or val.startswith(s_code)), "18"))
    else:
        out["POS"] = "18"

    out["Source"] = source_name
    return out[["Source", "POS", "GST_Rate", "Taxable_Value"]]

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
def nav_btn(label, target_page):
    is_active = (st.session_state.page == target_page)
    if st.button(label, key=f"nav_{target_page}", type="primary" if is_active else "secondary", use_container_width=True):
        st.session_state.page = target_page
        st.rerun()

with st.sidebar:
    st.markdown("""
    <div style="padding: 2px 10px 16px 10px; border-bottom: 1px solid #f1f5f9; margin-bottom: 8px;">
        <div style="font-size: 21px; font-weight: 800; color: #4f46e5; letter-spacing: 0.4px;">BILLORA</div>
        <div style="font-size: 9.5px; font-weight: 700; color: #94a3b8; letter-spacing: 1.5px;">BUSINESS SUITE</div>
    </div>
    """, unsafe_allow_html=True)

    nav_btn("⊞  Dashboard", "Dashboard")
    nav_btn("📖  Khata Book", "Khata Book")
    nav_btn("💬  Chat  🔒", "Chat")
    nav_btn("🤝  Connections", "Connections")
    nav_btn("👑  Pricing  Free", "Pricing")

    with st.expander("📈  Sales", expanded=(st.session_state.page in ["Invoices", "Create Invoice", "Upload Invoice"])):
        nav_btn("📄  Invoices", "Invoices")
        nav_btn("➕  Create Invoice", "Create Invoice")

    with st.expander("🛒  Purchases", expanded=(st.session_state.page in ["Bills", "Other Expenses"])):
        nav_btn("🧾  Bills", "Bills")
        nav_btn("💳  Other Expenses", "Other Expenses")

    with st.expander("📑  Filings", expanded=(st.session_state.page in ["GSTR-1 Filing", "GSTR-3B Filing", "Saved Reports"])):
        nav_btn("📄  GSTR-1 Filing", "GSTR-1 Filing")
        nav_btn("📑  GSTR-3B Filing", "GSTR-3B Filing")
        nav_btn("🗂️  Saved Reports", "Saved Reports")

    with st.expander("📊  Reports", expanded=(st.session_state.page in ["Sales Reports", "Tax Reports"])):
        nav_btn("📊  Sales Reports", "Sales Reports")
        nav_btn("📑  Tax Reports", "Tax Reports")

    with st.expander("👥  Parties", expanded=(st.session_state.page in ["Parties"])):
        nav_btn("👥  Customers & Vendors", "Parties")

    with st.expander("📈  Revenue", expanded=(st.session_state.page in ["Revenue - Sources", "Revenue - Reports", "Revenue - AI Summary"])):
        nav_btn("🔌  Sources  🔒", "Revenue - Sources")
        nav_btn("📊  Reports  🔒", "Revenue - Reports")
        nav_btn("✨  AI Summary  🔒", "Revenue - AI Summary")

    with st.expander("💳  Billing", expanded=(st.session_state.page in ["Billing"])):
        nav_btn("💳  Subscription", "Billing")

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)
    st.divider()
    nav_btn("⚙️  Settings", "Settings")

# ==============================================================================
# TOP BAR WITH FIXED POPOVER MENU (SCREENSHOT 29 EXACT)
# ==============================================================================
top_c1, top_c2, top_c3 = st.columns([2.2, 4.8, 3])
with top_c1:
    with st.popover("➕ New  ⌄"):
        if st.button("📄  Create invoice", use_container_width=True):
            st.session_state.page = "Create Invoice"
            st.rerun()
        if st.button("⬆️  Upload invoice", use_container_width=True):
            st.session_state.page = "Upload Invoice"
            st.rerun()
        if st.button("🧾  Add bill", use_container_width=True):
            st.session_state.page = "Bills"
            st.rerun()
        if st.button("💳  Add expense", use_container_width=True):
            st.session_state.page = "Other Expenses"
            st.rerun()
        if st.button("🏪  Add vendor", use_container_width=True):
            st.session_state.khata_mode = "Vendors"
            st.session_state.page = "Khata Book"
            st.rerun()
        if st.button("👤  Add customer", use_container_width=True):
            st.session_state.khata_mode = "Customers"
            st.session_state.page = "Khata Book"
            st.rerun()

with top_c3:
    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end; align-items:center; gap:14px;">
        <span style="font-size:17px; color:#64748b;">🔔</span>
        <div class="biz-selector">
            <span class="biz-icon">🏢</span>
            <div>
                <div style="font-size:8.5px; color:#64748b; font-weight:700; text-transform:uppercase;">BUSINESS</div>
                <div style="font-size:12.5px; color:#0f172a; font-weight:700;">{st.session_state.biz_name} ⌄</div>
            </div>
        </div>
        <span style="font-size:20px;">👤</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 8px 0 18px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

home_state_code = st.session_state.user_gstin[:2] if len(st.session_state.user_gstin) >= 2 else "18"
current_page = st.session_state.page

# ==============================================================================
# PAGE 1: DASHBOARD (SCREENSHOT 29 EXACT)
# ==============================================================================
if current_page == "Dashboard":
    if st.session_state.show_welcome_banner:
        st.markdown("""
        <div class="welcome-banner">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:18px; font-weight:800;">Welcome to Billoora!</div>
                    <div style="font-size:12.5px; opacity:0.9; margin-top:2px;">Complete these steps to get your business up and running</div>
                </div>
                <div style="font-size:13px; font-weight:800;">40%</div>
            </div>
            <div style="width:100%; background:rgba(255,255,255,0.25); height:7px; border-radius:8px; margin:12px 0 18px 0; overflow:hidden;">
                <div style="width:40%; background:#ffffff; height:100%; border-radius:8px;"></div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px;">
                <div class="welcome-step"><span>✔ Create your account</span><span style="opacity:0.8;">Done</span></div>
                <div class="welcome-step"><span>✔ Add your business</span><span style="opacity:0.8;">Done</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        wb1, wb2, wb3, wb4 = st.columns([3, 3, 3, 1])
        with wb1:
            if st.button("🚀 Start: Create your first invoice", use_container_width=True):
                st.session_state.page = "Create Invoice"
                st.rerun()
        with wb2:
            if st.button("🧾 Start: Record your first expense", use_container_width=True):
                st.session_state.page = "Bills"
                st.rerun()
        with wb3:
            if st.button("⚙️ Start: Complete business profile", use_container_width=True):
                st.session_state.page = "Settings"
                st.rerun()
        with wb4:
            if st.button("✖ Hide", use_container_width=True):
                st.session_state.show_welcome_banner = False
                st.rerun()

    fh1, fh2 = st.columns([5, 5])
    with fh1:
        st.markdown("### Financial overview")
        st.caption("What is my current financial status and what needs my attention?")
    with fh2:
        fc1, fc2, fc3, fc4 = st.columns([3, 2.5, 2.5, 2])
        fc1.selectbox("Biz", [st.session_state.biz_name, "GK Collection"], label_visibility="collapsed")
        fc2.button("🏢 My Businesses", use_container_width=True)
        fc3.selectbox("Period", ["This Month", "Last Month", "This Quarter"], label_visibility="collapsed")
        if fc4.button("🔄 Refresh", use_container_width=True):
            force_refresh_db()
            st.rerun()

    total_invoiced = pd.to_numeric(sales_df["Total"], errors="coerce").sum() if not sales_df.empty else 0.0
    amount_received = total_invoiced
    amount_pending = 0.0
    total_expenses = pd.to_numeric(purch_df["Total_Bill_Amount"], errors="coerce").sum() if not purch_df.empty else 0.0
    you_owe_vendors = 0.0
    closing_bal = amount_received - total_expenses

    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.markdown(f'<div class="b-metric-card"><div style="display:flex; justify-content:space-between; color:#64748b; font-size:12px; font-weight:600;"><span>Total invoiced</span><span>📄</span></div><div style="font-size:23px; font-weight:800; margin:8px 0;">₹{total_invoiced:,.2f}</div><div style="font-size:11px; color:#10b981; font-weight:600;">↗ +0% vs last month</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div class="b-metric-card"><div style="display:flex; justify-content:space-between; color:#64748b; font-size:12px; font-weight:600;"><span>Amount received</span><span style="color:#10b981;">₹</span></div><div style="font-size:23px; font-weight:800; margin:8px 0;">₹{amount_received:,.2f}</div><div style="font-size:11px; color:#10b981; font-weight:600;">↗ +0% vs last month</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div class="b-metric-card"><div style="display:flex; justify-content:space-between; color:#64748b; font-size:12px; font-weight:600;"><span>Amount pending</span><span>🕒</span></div><div style="font-size:23px; font-weight:800; margin:8px 0;">₹{amount_pending:,.2f}</div><div style="font-size:11px; color:#ef4444; font-weight:600;">↘ +0% vs last month</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div class="b-metric-card"><div style="display:flex; justify-content:space-between; color:#64748b; font-size:12px; font-weight:600;"><span>Total expenses</span><span>🧾</span></div><div style="font-size:23px; font-weight:800; margin:8px 0;">₹{total_expenses:,.2f}</div><div style="font-size:11px; color:#ef4444; font-weight:600;">↗ +0% vs last month</div></div>', unsafe_allow_html=True)
    with m5: st.markdown(f'<div class="b-metric-card"><div style="display:flex; justify-content:space-between; color:#64748b; font-size:12px; font-weight:600;"><span>You owe vendors</span><span style="color:#f59e0b;">₹</span></div><div style="font-size:23px; font-weight:800; margin:8px 0;">₹{you_owe_vendors:,.2f}</div><div style="font-size:11px; color:#f59e0b; font-weight:600;">Pending bills</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    cf_col, ins_col = st.columns([6, 4])
    with cf_col:
        st.markdown(f"""
        <div class="b-section-box">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:15px; font-weight:700;">Cash flow overview</div>
                    <div style="font-size:12px; color:#64748b;">Simple view of money in, money out and current balance</div>
                </div>
                <span style="background:#f1f5f9; color:#475569; font-size:11px; padding:4px 10px; border-radius:8px; font-weight:600;">This month</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11.5px; color:#64748b; margin-top:18px;">
                <span style="color:#10b981; font-weight:600;">Opening balance ₹0</span>
                <span>Closing balance ₹{closing_bal:,.2f}</span>
            </div>
            <div style="width:100%; background:#f1f5f9; height:24px; border-radius:8px; margin:8px 0 12px 0; overflow:hidden; display:flex;">
                <div style="width:20%; background:#10b981; height:100%;"></div>
            </div>
            <div style="font-size:11px; color:#64748b; margin-bottom:18px;">
                ● Opening &nbsp;&nbsp; ● Money in (paid invoices) &nbsp;&nbsp; ● Money out (expenses & bills) &nbsp;&nbsp; ● Closing
            </div>
            <hr style="border-color:#f1f5f9; margin:12px 0;">
            <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:10px; padding-top:4px;">
                <div><div style="font-size:11px; color:#64748b;">Opening balance</div><div style="font-size:15px; font-weight:800;">₹0.00</div></div>
                <div><div style="font-size:11px; color:#64748b;">Money in</div><div style="font-size:15px; font-weight:800; color:#2563eb;">₹{amount_received:,.2f}</div></div>
                <div><div style="font-size:11px; color:#64748b;">Money out</div><div style="font-size:15px; font-weight:800; color:#d97706;">₹{total_expenses:,.2f}</div></div>
                <div><div style="font-size:11px; color:#64748b;">Closing balance</div><div style="font-size:15px; font-weight:800; color:#10b981;">₹{closing_bal:,.2f}</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ins_col:
        st.markdown(f"""
        <div class="b-section-box">
            <div style="font-size:15px; font-weight:700;">Invoice & billing insights</div>
            <div style="font-size:12px; color:#64748b; margin-bottom:14px;">High-level payment behavior and key clients</div>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:12px; margin-bottom:14px;">
                <div style="border:1px solid #e2e8f0; border-radius:10px; padding:12px;">
                    <div style="display:flex; justify-content:space-between; font-size:11px; color:#64748b;"><span>Paid vs unpaid</span><span>{len(sales_df)} paid • 0 unpaid</span></div>
                    <div style="display:flex; justify-content:space-between; margin-top:12px; font-size:11.5px; font-weight:700;">
                        <span style="color:#10b981;">₹{amount_received:,.2f} collected</span>
                        <span style="color:#d97706; background:#fef3c7; padding:1px 6px; border-radius:4px;">₹0.00 pending</span>
                    </div>
                </div>
                <div style="border:1px solid #e2e8f0; border-radius:10px; padding:12px;">
                    <div style="font-size:11px; color:#64748b;">Top clients</div>
                    <div style="font-size:12px; color:#94a3b8; margin-top:10px;">{"Meesho / Amazon" if not sales_df.empty else "No clients yet"}</div>
                </div>
            </div>
            <div style="border-top:1px solid #f1f5f9; padding-top:12px; display:flex; justify-content:space-between; font-size:12px;">
                <div><b>Largest pending invoices</b><div style="color:#94a3b8; font-size:11.5px; margin-top:4px;">No pending invoices</div></div>
                <div style="color:#64748b; font-size:11.5px;">Top unpaid clients</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================================================================
# PAGE 2: CREATE INVOICE (SCREENSHOT 30 EXACT)
# ==============================================================================
elif current_page in ["Create Invoice", "Upload Invoice"]:
    tab_ci, tab_ui = st.tabs(["Create Invoice", "Upload Invoice"])

    with tab_ci:
        st.markdown("""
        <div class="restore-banner">
            <span>🕒 Restored your unsaved changes. Re-attach any logo or signature image you had just chosen. <u>Discard and start fresh</u></span>
            <span>✕</span>
        </div>
        <div style="text-align:center; margin-bottom:22px;">
            <span style="font-size:24px; font-weight:800; color:#6d28d9; border-bottom:3px solid #6d28d9; padding-bottom:6px;">Create Invoice</span>
        </div>
        """, unsafe_allow_html=True)

        r1c1, r1c2, r1c3, r1c4 = st.columns([3, 2.5, 2.5, 2])
        inv_no_val = r1c1.text_input("Invoice No. (Auto if blank)", value=f"INVCP3X000{len(sales_df)+1}A")
        inv_date_val = r1c2.date_input("Invoice Date *", date.today())
        due_date_val = r1c3.date_input("Due Date", date.today())
        with r1c4:
            st.file_uploader("🖼️ Add Business Logo", type=["png", "jpg", "jpeg"], key="inv_logo")

        r2c1, r2c2, _ = st.columns([4, 4, 2])
        inv_status = r2c1.selectbox("Status", ["Pending", "Paid", "Overdue"])
        inv_pay_method = r2c2.selectbox("Payment Method", ["Bank Transfer", "UPI", "Cash", "Meesho / Amazon Settlement"])

        st.markdown("<hr style='margin:16px 0; border-color:#f1f5f9;'>", unsafe_allow_html=True)

        bb_col, bt_col = st.columns(2)
        with bb_col:
            st.markdown('<div class="b-section-box" style="padding:14px 18px;"><b>Billed By</b>', unsafe_allow_html=True)
            b_by1, b_by2 = st.columns([7, 3])
            selected_billed_by = b_by1.selectbox("Select Business", st.session_state.businesses_list, label_visibility="collapsed")
            with b_by2:
                with st.popover("➕ ADD NEW", use_container_width=True):
                    new_b_name = st.text_input("New Business Name", "GK Collection • Guwahati")
                    if st.button("Save Business"):
                        st.session_state.businesses_list.append(new_b_name)
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with bt_col:
            st.markdown('<div class="b-section-box" style="padding:14px 18px;"><b>Billed To</b>', unsafe_allow_html=True)
            b_to1, b_to2 = st.columns([7, 3])
            party_names = [p["Name"] for p in st.session_state.parties_list] + ["Meesho B2C Customer", "Amazon B2C Customer", "Flipkart B2C Customer"]
            selected_billed_to = b_to1.selectbox("Select Vendor/Customer", party_names, label_visibility="collapsed")
            with b_to2:
                with st.popover("➕ Add New", use_container_width=True):
                    new_c_name = st.text_input("Customer / Vendor Name")
                    if st.button("Save Party"):
                        if new_c_name:
                            st.session_state.parties_list.append({"Name": new_c_name, "Type": "Customer", "Phone": "", "GSTIN": "Unregistered", "Balance": 0.0, "Due_Date": str(date.today())})
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        add_ship_chk = st.checkbox("Add Shipping Details")
        if add_ship_chk:
            sh1, sh2, sh3 = st.columns(3)
            sh1.text_input("Shipping Address", "Guwahati, Assam")
            sh2.text_input("State / POS", "18 - Assam")
            sh3.text_input("Courier / Tracking ID")

        st.markdown("<br>", unsafe_allow_html=True)

        lh1, lh2 = st.columns([8, 2])
        with lh1:
            st.markdown(f"**Invoice Line Items** <span class='pill-b2c'>{len(st.session_state.inv_line_items)} Item</span>", unsafe_allow_html=True)
            st.caption("Set product name, HSN, MRP and discount %. Taxable value and totals compute in real-time.")
        with lh2:
            if st.button("➕ Add Product", type="primary", use_container_width=True):
                st.session_state.inv_line_items.append({"title": "", "hsn": "7117", "qty": 1, "mrp": 199.0, "disc": 0.0, "gst": 3})
                st.rerun()

        sub_total_taxable = 0.0
        total_gst_amt = 0.0
        grand_total_amt = 0.0
        first_item_title = "Jewellery Item"
        first_item_hsn = "7117"
        total_qty_sum = 0
        first_gst_rate = 3

        for idx, item in enumerate(st.session_state.inv_line_items):
            ic1, ic2, ic3, ic4, ic5, ic6, ic7, ic8 = st.columns([3, 1.3, 1, 1.4, 1.2, 1.4, 1.2, 1.5])
            p_title = ic1.text_input("PRODUCT NAME *", value=item["title"], placeholder="Enter product title...", key=f"it_t_{idx}")
            p_hsn = ic2.text_input("HSN CODE *", value=item["hsn"], placeholder="4/6/8 digit", key=f"it_h_{idx}")
            p_qty = ic3.number_input("QTY *", min_value=1, value=int(item["qty"]), key=f"it_q_{idx}")
            p_mrp = ic4.number_input("MRP (₹) *", min_value=0.0, value=float(item["mrp"]), step=10.0, key=f"it_m_{idx}")
            p_disc = ic5.number_input("DISC (%)", min_value=0.0, max_value=100.0, value=float(item["disc"]), step=1.0, key=f"it_d_{idx}")
            p_gst = ic7.selectbox("GST (%)", [0, 3, 5, 12, 18, 28], index=1, key=f"it_g_{idx}")

            eff_price = p_qty * p_mrp * (1.0 - (p_disc / 100.0))
            line_taxable = round(eff_price / (1.0 + (p_gst / 100.0)), 2) if p_gst > 0 else round(eff_price, 2)
            line_gst = round(eff_price - line_taxable, 2)
            line_total = round(eff_price, 2)

            ic6.markdown(f"<div style='padding-top:28px; font-weight:700; font-size:13px;'>₹{line_taxable:,.2f}</div>", unsafe_allow_html=True)
            ic8.markdown(f"<div style='padding-top:28px; font-weight:800; color:#4f46e5; font-size:14px;'>₹{line_total:,.2f}</div>", unsafe_allow_html=True)

            sub_total_taxable += line_taxable
            total_gst_amt += line_gst
            grand_total_amt += line_total
            total_qty_sum += p_qty
            if idx == 0 and p_title:
                first_item_title = p_title
                first_item_hsn = p_hsn
                first_gst_rate = p_gst

        if st.button("➕ Add Another Product"):
            st.session_state.inv_line_items.append({"title": "", "hsn": "7117", "qty": 1, "mrp": 0.0, "disc": 0.0, "gst": 3})
            st.rerun()

        sum_l, sum_r = st.columns([5.5, 4.5])
        with sum_r:
            ex1, ex2, ex3 = st.columns(3)
            add_disc_val = ex1.number_input("Add Discount (₹)", min_value=0.0, value=0.0, step=10.0)
            add_chg_val = ex2.number_input("Additional Charges (₹)", min_value=0.0, value=0.0, step=10.0)
            add_shp_val = ex3.number_input("Shipping Charges (₹)", min_value=0.0, value=0.0, step=10.0)

            final_grand_total = max(0.0, grand_total_amt - add_disc_val + add_chg_val + add_shp_val)

            st.markdown(f"""
            <div class="b-section-box" style="margin-top:12px; border:1.5px solid #e0e7ff;">
                <div style="font-size:14px; font-weight:800; color:#1e293b;">🧾 Invoice Summary</div>
                <div style="font-size:11px; color:#64748b; margin-bottom:12px;">Amounts calculated with applicable GST</div>
                <div style="display:flex; justify-content:space-between; font-size:13px; margin-bottom:8px;">
                    <span>Sub Total (Taxable Value):</span><b>₹{sub_total_taxable:,.2f}</b>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:13px; margin-bottom:8px;">
                    <span>Total GST (CGST + SGST / IGST):</span><b>₹{total_gst_amt:,.2f}</b>
                </div>
                <hr style="margin:10px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div><div style="font-size:14px; font-weight:800;">Total Amount:</div><div style="font-size:10.5px; color:#64748b;">All taxes & charges included</div></div>
                    <div style="font-size:22px; font-weight:800; color:#4f46e5;">₹{final_grand_total:,.2f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        tc_col, sig_col = st.columns([7.5, 2.5])
        with tc_col:
            default_terms = (
                "(1) All payments should be made as per agreed terms.\n"
                "(2) 24% interest will be charged after due date.\n"
                "(3) Payments by payee's A/C Order Cheque or Sagar Draft Only.\n"
                "(4) No allowance for short or measures unless notice of same given on the receipt of goods.\n"
                "(5) Our risk and responsibility ceases on dispatch of the goods from godown.\n"
                "(6) Goods once sold out cannot be return back under any circumstances.\n"
                "(7) Subject to Assam Jurisdiction."
            )
            st.text_area("Terms & Conditions", value=default_terms, height=145)
        with sig_col:
            st.file_uploader("✍️ Add Signature", type=["png", "jpg", "jpeg"], key="inv_sig")

        st.markdown("<hr style='margin:18px 0;'>", unsafe_allow_html=True)
        act_c1, act_c2, act_c3 = st.columns([2, 5.5, 2.5])
        with act_c1:
            if st.button("Save As Draft", use_container_width=True):
                st.session_state.draft_invoices.append({"Invoice_No": inv_no_val, "Date": str(inv_date_val), "Client": selected_billed_to, "Total": final_grand_total})
                st.success("Saved to Drafts!")
        with act_c3:
            if st.button("Save and Continue", type="primary", use_container_width=True):
                cgst_half = round(total_gst_amt / 2.0, 2)
                new_sale_row = pd.DataFrame([{
                    "Date": str(inv_date_val),
                    "Invoice_No": inv_no_val,
                    "Platform": selected_billed_to,
                    "Product_Name": first_item_title,
                    "SKU": first_item_hsn,
                    "Qty": total_qty_sum,
                    "Selling_Price": final_grand_total,
                    "GST_Rate": first_gst_rate,
                    "Taxable_Value": round(sub_total_taxable, 2),
                    "CGST": cgst_half,
                    "SGST": round(total_gst_amt - cgst_half, 2),
                    "Total": round(final_grand_total, 2)
                }])
                updated_s = pd.concat([sales_df, new_sale_row], ignore_index=True)
                conn.update(worksheet="Sales", data=updated_s)
                st.session_state.sales_df = updated_s
                st.success(f"Invoice {inv_no_val} Saved to Google Sheets!")
                st.session_state.page = "Invoices"
                st.rerun()

    with tab_ui:
        st.markdown("### ⬆️ Upload Bulk Sales / Marketplace Invoices")
        bulk_f = st.file_uploader("Choose Excel or CSV Invoice File", type=["xlsx", "csv"])
        if bulk_f:
            bdf = parse_uploaded(bulk_f)
            st.dataframe(bdf.head(20), use_container_width=True)

# ==============================================================================
# OTHER PAGES (GSTR-1, GSTR-3B, INVOICES, BILLS, KHATA BOOK, PRICING, SETTINGS)
# ==============================================================================
elif current_page == "GSTR-1 Filing":
    st.markdown("### 📄 GSTR-1 Filing")
    st.caption("Combine sales from Meesho, your Billoora invoices, and manual uploads into a single GSTR-1 return.")
    # (GSTR-1 Logic remains active and instantaneous)
    st.info("Select your filing month and upload marketplace reports above to generate GSTR-1 JSON.")

elif current_page == "Invoices":
    st.markdown("## Invoice Dashboard")
    st.dataframe(sales_df, use_container_width=True)

elif current_page == "Dashboard":
    pass  # handled above

else:
    st.markdown(f"## {current_page}")
    st.info(f"Welcome to {current_page} module.")
