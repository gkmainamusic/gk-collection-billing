import streamlit as st
import pandas as pd
import json
import io
from datetime import date, datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="BILLORA — Business Suite", page_icon="🟣", layout="wide", initial_sidebar_state="expanded")

# --- SESSION STATE INITIALIZATION ---
if "page" not in st.session_state:
    st.session_state.page = "GSTR-1 Filing"
if "nav_sales_open" not in st.session_state:
    st.session_state.nav_sales_open = False
if "nav_purch_open" not in st.session_state:
    st.session_state.nav_purch_open = False
if "nav_filings_open" not in st.session_state:
    st.session_state.nav_filings_open = True
if "nav_rev_open" not in st.session_state:
    st.session_state.nav_rev_open = False
if "khata_mode" not in st.session_state:
    st.session_state.khata_mode = "Customers"
if "parties_list" not in st.session_state:
    st.session_state.parties_list = [
        {"Name": "Meesho Customer Pool", "Type": "Customer", "Phone": "9876543210", "GSTIN": "Unregistered", "Balance": 0.0, "Due_Date": str(date.today())},
        {"Name": "Fancy Bazaar Wholesale Hub", "Type": "Vendor", "Phone": "9123456789", "GSTIN": "18AABCF1234D1Z5", "Balance": 0.0, "Due_Date": str(date.today())}
    ]
if "saved_reports" not in st.session_state:
    st.session_state.saved_reports = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "text": "Namaste! Main Billoora AI Assistant hoon. Aap mujhse GSTR-1, GSTR-3B, ITC calculation ya Meesho/Amazon B2C invoices ke baare mein kuch bhi pooch sakte hain."}
    ]
if "biz_name" not in st.session_state:
    st.session_state.biz_name = "GK Collection"
if "user_gstin" not in st.session_state:
    st.session_state.user_gstin = "18AAAAA0000A1Z5"

# --- EXACT BILLOORA CSS STYLING ---
st.markdown("""
<style>
    /* Global App Background */
    .stApp { background-color: #f4f6fa; color: #0f172a; font-family: 'Inter', system-ui, sans-serif; }
    .block-container { padding-top: 1.2rem !important; padding-bottom: 3rem !important; max-width: 98% !important; }

    /* Left Sidebar Exact White Styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0 !important;
        width: 255px !important;
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 1rem !important; padding-left: 0.8rem !important; padding-right: 0.8rem !important; }

    /* Sidebar Buttons as Clean Menu Items */
    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        text-align: left !important;
        justify-content: flex-start !important;
        background-color: transparent !important;
        color: #475569 !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        padding: 7px 12px !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        margin-bottom: 2px !important;
        transition: all 0.15s ease;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    /* Active Sidebar Button (Highlighted Purple Box like Screenshot) */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background-color: #f5f3ff !important;
        color: #4f46e5 !important;
        border: 1px solid #6366f1 !important;
        font-weight: 600 !important;
    }

    /* Top Header Bar */
    .billora-topbar {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .new-btn-badge {
        background-color: #0d9488;
        color: white;
        font-weight: 600;
        font-size: 13px;
        padding: 7px 16px;
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .biz-selector {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 5px 14px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
    }
    .biz-icon {
        background: #4f46e5;
        color: white;
        border-radius: 6px;
        padding: 5px 8px;
        font-size: 13px;
        font-weight: 700;
    }

    /* White Containers & Metric Cards */
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
        padding: 18px 20px;
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
        border: 1.5px solid #34d399;
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
        padding: 45px 20px;
        text-align: center;
        color: #64748b;
        margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet_name, columns):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=5)
        if df.empty:
            return pd.DataFrame(columns=columns)
        df = df.dropna(how="all")
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns]
    except Exception:
        return pd.DataFrame(columns=columns)

sales_cols = ["Date", "Invoice_No", "Platform", "Product_Name", "SKU", "Qty", "Selling_Price", "GST_Rate", "Taxable_Value", "CGST", "SGST", "Total"]
purch_cols = ["Date", "Bill_No", "Supplier_Name", "Category", "Total_Bill_Amount", "GST_Rate", "Taxable_Amount", "ITC_Claimed"]
cat_cols = ["SKU", "Product_Name", "Buy_Cost", "Packaging_Cost", "Platform_Fee", "Profit_Margin", "Selling_Price", "Suggested_MRP", "GST_Rate", "Net_Weight_g"]

sales_df = load_data("Sales", sales_cols)
purch_df = load_data("Purchases", purch_cols)
cat_df = load_data("Catalog", cat_cols)

# --- UNIVERSAL B2C MARKETPLACE PARSER ---
STATE_MAP = {
    "JAMMU AND KASHMIR": "01", "HIMACHAL PRADESH": "02", "PUNJAB": "03", "CHANDIGARH": "04",
    "UTTARAKHAND": "05", "HARYANA": "06", "DELHI": "07", "RAJASTHAN": "08", "UTTAR PRADESH": "09",
    "BIHAR": "10", "SIKKIM": "11", "ARUNACHAL PRADESH": "12", "NAGALAND": "13", "MANIPUR": "14",
    "MIZORAM": "15", "TRIPURA": "16", "MEGHALAYA": "17", "ASSAM": "18", "WEST BENGAL": "19",
    "JHARKHAND": "20", "ODISHA": "21", "CHHATTISGARH": "22", "MADHYA PRADESH": "23",
    "GUJARAT": "24", "MAHARASHTRA": "27", "KARNATAKA": "29", "GOA": "30", "KERALA": "32",
    "TAMIL NADU": "33", "TELANGANA": "36", "ANDHRA PRADESH": "37"
}

def read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return pd.DataFrame()
    try:
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error reading {uploaded_file.name}: {e}")
        return pd.DataFrame()

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
# LEFT SIDEBAR NAVIGATION (EXACT BILLOORA REPLICA FROM SCREENSHOTS)
# ==============================================================================
def nav_item(label, target_page, indent=False):
    is_active = (st.session_state.page == target_page)
    display_lbl = f"    {label}" if indent else label
    if st.button(display_lbl, key=f"nav_{target_page}_{label}", type="primary" if is_active else "secondary", use_container_width=True):
        st.session_state.page = target_page
        st.rerun()

with st.sidebar:
    st.markdown("""
    <div style="padding: 4px 8px 16px 8px;">
        <div style="font-size: 21px; font-weight: 800; color: #4f46e5; letter-spacing: 0.5px;">BILLORA</div>
        <div style="font-size: 9.5px; font-weight: 700; color: #94a3b8; letter-spacing: 1.5px;">BUSINESS SUITE</div>
    </div>
    """, unsafe_allow_html=True)

    nav_item("⊞  Dashboard", "Dashboard")
    nav_item("📖  Khata Book", "Khata Book")
    nav_item("💬  Chat                       🔒", "Chat")
    nav_item("🤝  Connections", "Connections")
    nav_item("👑  Pricing                 Free", "Pricing")

    # Collapsible Sales Group
    sales_arrow = "⌄" if st.session_state.nav_sales_open else "›"
    if st.button(f"📈  Sales                        {sales_arrow}", key="grp_sales", use_container_width=True):
        st.session_state.nav_sales_open = not st.session_state.nav_sales_open
        st.rerun()
    if st.session_state.nav_sales_open:
        nav_item("📄  Invoices", "Invoices", indent=True)

    # Collapsible Purchases Group
    purch_arrow = "⌄" if st.session_state.nav_purch_open else "›"
    if st.button(f"🛒  Purchases                 {purch_arrow}", key="grp_purch", use_container_width=True):
        st.session_state.nav_purch_open = not st.session_state.nav_purch_open
        st.rerun()
    if st.session_state.nav_purch_open:
        nav_item("🧾  Bills", "Bills", indent=True)
        nav_item("💳  Other Expenses", "Other Expenses", indent=True)

    # Collapsible Filings Group
    fil_arrow = "⌄" if st.session_state.nav_filings_open else "›"
    if st.button(f"📑  Filings                      {fil_arrow}", key="grp_filings", use_container_width=True):
        st.session_state.nav_filings_open = not st.session_state.nav_filings_open
        st.rerun()
    if st.session_state.nav_filings_open:
        nav_item("📄  GSTR-1 Filing", "GSTR-1 Filing", indent=True)
        nav_item("📑  GSTR-3B Filing", "GSTR-3B Filing", indent=True)
        nav_item("🗂️  Saved Reports", "Saved Reports", indent=True)

    nav_item("📊  Reports                     ›", "Reports")
    nav_item("👥  Parties                      ›", "Parties")

    # Collapsible Revenue Group
    rev_arrow = "⌄" if st.session_state.nav_rev_open else "›"
    if st.button(f"📈  Revenue                    {rev_arrow}", key="grp_rev", use_container_width=True):
        st.session_state.nav_rev_open = not st.session_state.nav_rev_open
        st.rerun()
    if st.session_state.nav_rev_open:
        nav_item("🔌  Sources                  🔒", "Revenue - Sources", indent=True)
        nav_item("📊  Reports                  🔒", "Revenue - Reports", indent=True)
        nav_item("✨  AI Summary            🔒", "Revenue - AI Summary", indent=True)

    nav_item("💳  Billing                       ›", "Billing")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    nav_item("⚙️  Settings", "Settings")

# ==============================================================================
# TOP BAR (+ New Dropdown & Business Profile Pill like Screenshot)
# ==============================================================================
top_c1, top_c2, top_c3 = st.columns([2, 5, 3])
with top_c1:
    with st.popover("➕ New  ⌄"):
        st.markdown("**Quick Create**")
        if st.button("📄 + Issue Sale Invoice", use_container_width=True):
            st.session_state.nav_sales_open = True
            st.session_state.page = "Invoices"
            st.rerun()
        if st.button("🧾 + Add Purchase Bill", use_container_width=True):
            st.session_state.nav_purch_open = True
            st.session_state.page = "Bills"
            st.rerun()
        if st.button("📄 File GSTR-1 Return", use_container_width=True):
            st.session_state.nav_filings_open = True
            st.session_state.page = "GSTR-1 Filing"
            st.rerun()
        if st.button("👤 + Add Customer / Vendor", use_container_width=True):
            st.session_state.page = "Khata Book"
            st.rerun()

with top_c3:
    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end; align-items:center; gap:14px;">
        <span style="font-size:18px; color:#64748b;">🔔</span>
        <div class="biz-selector">
            <span class="biz-icon">🏢</span>
            <div>
                <div style="font-size:9px; color:#64748b; font-weight:700; text-transform:uppercase;">BUSINESS</div>
                <div style="font-size:12.5px; color:#0f172a; font-weight:600;">{st.session_state.biz_name} ({st.session_state.user_gstin[:2]}) ⌄</div>
            </div>
        </div>
        <span style="font-size:22px;">👤</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 8px 0 20px 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)

home_state_code = st.session_state.user_gstin[:2] if len(st.session_state.user_gstin) >= 2 else "18"
current_page = st.session_state.page

# ==============================================================================
# PAGE 1: FILINGS -> GSTR-1 FILING (SCREENSHOT 1 EXACT REPLICA)
# ==============================================================================
if current_page == "GSTR-1 Filing":
    st.markdown("### 📄 GSTR-1 Filing")
    st.caption("Combine sales from Meesho, your Billoora invoices, and manual uploads into a single GSTR-1 return. Select one or more platforms below.")

    # Period Picker Box
    st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([3, 3, 3, 1])
    filing_type = f1.selectbox("Type of Filing *", ["Monthly", "Quarterly"], key="g1_type")
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    sel_month = f2.selectbox("Month *", months_list, index=9, key="g1_month")
    sel_year = f3.selectbox("Year *", ["2026", "2025", "2027"], index=0, key="g1_year")
    with f4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("Reset", key="g1_reset", use_container_width=True):
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    fp_code = f"{str(months_list.index(sel_month) + 1).zfill(2)}{sel_year}"

    # 5 Platform Cards Row
    st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
    st.markdown("**Platforms**")
    c_m, c_f, c_a, c_b, c_man = st.columns(5)

    with c_m:
        st.markdown("""
        <div class="b-plat-card-active">
            <div style="display:flex; justify-content:space-between;"><span class="pill-b2c">B2C • MONTHLY</span><span style="color:#10b981;">✔</span></div>
            <div style="font-weight:700; font-size:15px; margin-top:4px;">🛍️ Meesho</div>
            <div style="font-size:11.5px; color:#64748b; margin-top:4px;">From Meesho Supplier Panel → Payments → Tax Invoices & Reports.</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("✏️ Edit / Upload Data", use_container_width=True):
            m_sales_file = st.file_uploader("TCS Sales Report (tcs_sales.xlsx/csv)", type=["xlsx", "csv"], key="g1_ms")
            m_ret_file = st.file_uploader("TCS Sales Return (tcs_sales_return.xlsx)", type=["xlsx", "csv"], key="g1_mr")

    with c_f:
        st.markdown("""
        <div class="b-plat-card">
            <span class="pill-b2c">B2C • MONTHLY</span>
            <div style="font-weight:700; font-size:15px; margin-top:4px;">🛒 Flipkart</div>
            <div style="font-size:11.5px; color:#64748b; margin-top:4px;">From Flipkart Seller Hub → Reports → Sales Report.</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("⬆️ Upload Data", use_container_width=True):
            f_sales_file = st.file_uploader("Upload Flipkart B2C Sales Report", type=["xlsx", "csv"], key="g1_fs")

    with c_a:
        st.markdown("""
        <div class="b-plat-card">
            <span class="pill-b2c">B2C • MONTHLY</span>
            <div style="font-weight:700; font-size:15px; margin-top:4px;">📦 Amazon</div>
            <div style="font-size:11.5px; color:#64748b; margin-top:4px;">From Amazon Seller Central → Reports → Tax Document Library → MTR.</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("⬆️ Upload Data", use_container_width=True):
            a_sales_file = st.file_uploader("Upload Amazon MTR B2C Report", type=["xlsx", "csv"], key="g1_as")

    with c_b:
        st.markdown("""
        <div class="b-plat-card">
            <span class="pill-b2c">Invoices • MONTHLY</span>
            <div style="font-weight:700; font-size:15px; margin-top:4px;">🏢 Billoora</div>
            <div style="font-size:11.5px; color:#64748b; margin-top:4px;">Include sales invoices you've raised in Billoora during this period.</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("📅 Select Date", use_container_width=True):
            inc_billoora = st.checkbox("Include Billoora Google Sheet Invoices", value=True, key="g1_inc_b")
            st.caption(f"Total Saved Invoices in DB: {len(sales_df)}")

    with c_man:
        st.markdown("""
        <div class="b-plat-card">
            <span class="pill-b2c">Upload • MONTHLY</span>
            <div style="font-weight:700; font-size:15px; margin-top:4px;">📄 Manual</div>
            <div style="font-size:11.5px; color:#64748b; margin-top:4px;">Upload an Excel of sales that live outside Billoora or the e-commerce...</div>
        </div>
        """, unsafe_allow_html=True)
        with st.popover("⬆️ Upload Data", use_container_width=True):
            man_file = st.file_uploader("Upload Manual B2C Excel / CSV", type=["xlsx", "csv"], key="g1_man")

    ab1, ab2 = st.columns([8, 2])
    with ab2:
        analyze_clicked = st.button("Analyze", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Process GSTR-1 Data
    dfs = []
    if m_sales_file: dfs.append(standardize_b2c_df(read_uploaded_file(m_sales_file), "Meesho", 1))
    if m_ret_file: dfs.append(standardize_b2c_df(read_uploaded_file(m_ret_file), "Meesho Return", -1))
    if f_sales_file: dfs.append(standardize_b2c_df(read_uploaded_file(f_sales_file), "Flipkart", 1))
    if a_sales_file: dfs.append(standardize_b2c_df(read_uploaded_file(a_sales_file), "Amazon", 1))
    if man_file: dfs.append(standardize_b2c_df(read_uploaded_file(man_file), "Manual", 1))
    if inc_billoora and not sales_df.empty:
        db_temp = pd.DataFrame()
        db_temp["Source"] = "Billoora"
        db_temp["POS"] = home_state_code
        db_temp["GST_Rate"] = pd.to_numeric(sales_df["GST_Rate"], errors="coerce").fillna(3.0)
        db_temp["Taxable_Value"] = pd.to_numeric(sales_df["Taxable_Value"], errors="coerce").fillna(0.0)
        dfs.append(db_temp)

    if dfs and (analyze_clicked or m_sales_file or f_sales_file or a_sales_file or man_file):
        combined = pd.concat(dfs, ignore_index=True)
        grouped = combined.groupby(["POS", "GST_Rate"], as_index=False)["Taxable_Value"].sum()
        grouped["Taxable_Value"] = grouped["Taxable_Value"].round(2)

        b2cs_entries, summary_rows = [], []
        for _, row in grouped.iterrows():
            pos, rt, txval = str(row["POS"]).zfill(2), float(row["GST_Rate"]), round(float(row["Taxable_Value"]), 2)
            if txval == 0: continue
            is_intra = (pos == home_state_code)
            if is_intra:
                camt, samt, iamt = round(txval * (rt / 200.0), 2), round(txval * (rt / 200.0), 2), 0.0
                b2cs_entries.append({"sply_ty": "INTRA", "pos": pos, "typ": "OE", "txval": txval, "rt": rt, "camt": camt, "samt": samt, "csamt": 0.0})
            else:
                iamt, camt, samt = round(txval * (rt / 100.0), 2), 0.0, 0.0
                b2cs_entries.append({"sply_ty": "INTER", "pos": pos, "typ": "OE", "txval": txval, "rt": rt, "iamt": iamt, "csamt": 0.0})
            summary_rows.append({"POS": pos, "Supply": "INTRA" if is_intra else "INTER", "GST Rate (%)": rt, "Taxable Value (₹)": txval, "IGST (₹)": iamt, "CGST (₹)": camt, "SGST (₹)": samt})

        sum_df = pd.DataFrame(summary_rows)
        st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
        st.markdown(f"#### GSTR-1 Analyzed Summary ({sel_month} {sel_year})")
        st.dataframe(sum_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        gstr1_json_str = json.dumps({"gstin": st.session_state.user_gstin, "fp": fp_code, "version": "GST3.1.6", "hash": "hash", "b2cs": b2cs_entries}, indent=2)
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
            sum_df.to_excel(writer, index=False, sheet_name="GSTR1_B2CS")

        if analyze_clicked:
            st.session_state.saved_reports.append({"Type": "GSTR-1", "Period": f"{sel_month} {sel_year}", "Generated_On": str(date.today()), "JSON": gstr1_json_str})
    else:
        st.markdown('<div class="empty-state-box">Choose your sources and click Analyze to begin.</div>', unsafe_allow_html=True)
        gstr1_json_str = json.dumps({"gstin": st.session_state.user_gstin, "fp": fp_code, "b2cs": []}, indent=2)
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
            pd.DataFrame().to_excel(writer, index=False)

    # Bottom Bar Buttons: Copy Totals | Download Excel | Download JSON (for GST portal)
    st.markdown("<br>", unsafe_allow_html=True)
    bot1, bot2, bot3, bot4 = st.columns([4, 2, 2, 2.5])
    with bot2:
        with st.popover("📋 Copy Totals", use_container_width=True):
            st.code(gstr1_json_str[:300])
    with bot3:
        st.download_button("⬇️ Download Excel", excel_buf.getvalue(), file_name=f"GSTR1_{fp_code}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with bot4:
        st.download_button("⬇️ Download JSON (for GST portal)", gstr1_json_str, file_name=f"GSTR1_{st.session_state.user_gstin}_{fp_code}.json", mime="application/json", type="primary", use_container_width=True)

# ==============================================================================
# PAGE 2: FILINGS -> GSTR-3B FILING (SCREENSHOT 2 EXACT REPLICA)
# ==============================================================================
elif current_page == "GSTR-3B Filing":
    st.markdown("### 📄 GSTR-3B Filing")
    st.caption("Outward supplies (Table 3.1/3.2) are re-computed from the same Meesho/Billoora/manual sources as GSTR-1. Eligible/ineligible ITC (Table 4) comes from the GSTR-2B JSON you download from the GST portal.")

    st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([3, 3, 3, 1])
    filing_type_3b = f1.selectbox("Type of Filing *", ["Monthly", "Quarterly"], key="g3_type")
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    sel_month_3b = f2.selectbox("Month *", months_list, index=9, key="g3_month")
    sel_year_3b = f3.selectbox("Year *", ["2026", "2025", "2027"], index=0, key="g3_year")
    with f4:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        st.button("Reset", key="g3_reset", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    fp_3b = f"{str(months_list.index(sel_month_3b) + 1).zfill(2)}{sel_year_3b}"

    # Green GSTR-2B Box
    st.markdown("""
    <div class="gstr2b-green-box">
        <div style="font-weight:700; color:#14532d; font-size:14px; margin-bottom:6px;">GSTR-2B (ITC source) <span style="color:#dc2626;">*</span></div>
        <div style="font-size:12px; color:#166534;">Download from GST Portal → Services → Returns → GSTR-2B → Download JSON.</div>
    </div>
    """, unsafe_allow_html=True)
    g2b_file = st.file_uploader("⬆️ Choose GSTR-2B .json file", type=["json"], key="g3_2b")

    # Outward Supply Sources Section
    st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
    st.markdown("#### Outward Supply Sources")
    chk_meesho_3b = st.checkbox("Meesho e-commerce sales (From Meesho Supplier Panel → Payments → Tax Invoices & Reports)", value=True)
    if chk_meesho_3b:
        u1, u2, u3 = st.columns(3)
        tcs_s_3b = u1.file_uploader("TCS Sales Report * (Choose tcs_sales.xlsx)", type=["xlsx", "csv"], key="3b_u1")
        tcs_r_3b = u2.file_uploader("TCS Sales Return Report * (Choose tcs_sales_return.xlsx)", type=["xlsx", "csv"], key="3b_u2")
        tax_i_3b = u3.file_uploader("Tax Invoice Details * (Choose Tax_invoice_details.xlsx)", type=["xlsx", "csv"], key="3b_u3")
    else:
        tcs_s_3b, tcs_r_3b, tax_i_3b = None, None, None

    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    chk_billoora_3b = st.checkbox("Billoora invoices (my own sales) — Date range is set automatically from the period picker above.", value=True)
    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)
    chk_manual_3b = st.checkbox("Manual sales upload — Same template as GSTR-1's manual upload.")
    man_3b_file = st.file_uploader("Upload Manual Sales Excel", type=["xlsx", "csv"], key="3b_man") if chk_manual_3b else None
    st.markdown('</div>', unsafe_allow_html=True)

    gen_3b = st.button("📄 Generate GSTR-3B", type="primary")

    if gen_3b or tcs_s_3b or chk_billoora_3b:
        out_dfs = []
        if tcs_s_3b: out_dfs.append(standardize_b2c_df(read_uploaded_file(tcs_s_3b), "Meesho", 1))
        if tcs_r_3b: out_dfs.append(standardize_b2c_df(read_uploaded_file(tcs_r_3b), "Meesho Return", -1))
        if man_3b_file: out_dfs.append(standardize_b2c_df(read_uploaded_file(man_3b_file), "Manual", 1))
        if chk_billoora_3b and not sales_df.empty:
            db_s = pd.DataFrame({"Source": "Billoora", "POS": home_state_code, "GST_Rate": pd.to_numeric(sales_df["GST_Rate"], errors="coerce").fillna(3.0), "Taxable_Value": pd.to_numeric(sales_df["Taxable_Value"], errors="coerce").fillna(0.0)})
            out_dfs.append(db_s)

        tx_tot, igst_tot, cgst_tot, sgst_tot = 0.0, 0.0, 0.0, 0.0
        if out_dfs:
            c3b = pd.concat(out_dfs, ignore_index=True)
            for _, r in c3b.iterrows():
                tx = float(r["Taxable_Value"])
                rt = float(r["GST_Rate"])
                tx_tot += tx
                if str(r["POS"]).zfill(2) == home_state_code:
                    cgst_tot += tx * (rt / 200.0)
                    sgst_tot += tx * (rt / 200.0)
                else:
                    igst_tot += tx * (rt / 100.0)

        itc_claim = pd.to_numeric(purch_df["ITC_Claimed"], errors="coerce").sum() if not purch_df.empty else 0.0
        st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
        st.markdown("#### Computed GSTR-3B Summary (Table 3.1 & Table 4 Eligible ITC)")
        st.dataframe(pd.DataFrame([{"Outward Taxable (₹)": round(tx_tot, 2), "Output IGST (₹)": round(igst_tot, 2), "Output CGST (₹)": round(cgst_tot, 2), "Output SGST (₹)": round(sgst_tot, 2), "Eligible ITC from Bills/2B (₹)": round(itc_claim, 2)}]), use_container_width=True)
        g3b_json = json.dumps({"gstin": st.session_state.user_gstin, "ret_period": fp_3b, "sup_details": {"osup_det": {"txval": round(tx_tot, 2), "iamt": round(igst_tot, 2), "camt": round(cgst_tot, 2), "samt": round(sgst_tot, 2)}}, "itc_elg": {"itc_avl": [{"ty": "OTH", "iamt": 0.0, "camt": round(itc_claim/2, 2), "samt": round(itc_claim/2, 2)}]}}, indent=2)
        st.download_button("⬇️ Download GSTR-3B JSON (for GST Portal)", g3b_json, file_name=f"GSTR3B_{fp_3b}.json", mime="application/json", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# PAGE 3: SALES -> INVOICES (SCREENSHOT 3 EXACT REPLICA)
# ==============================================================================
elif current_page == "Invoices":
    ih1, ih2 = st.columns([5, 5])
    with ih1:
        st.markdown("## Invoice Dashboard")
        st.caption("Manage and track all your invoices in one place")
    with ih2:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.download_button("📥 Export Data", sales_df.to_csv(index=False), "sales_invoices.csv", "text/csv", use_container_width=True)
        with b2:
            if st.button("📙 Export GSTR-3B", use_container_width=True):
                st.session_state.page = "GSTR-3B Filing"
                st.rerun()
        with b3:
            with st.popover("⬆️ Upload Invoice", use_container_width=True):
                up_inv = st.file_uploader("Upload Bulk Sales CSV/XLSX", type=["csv", "xlsx"])
        with b4:
            with st.popover("➕ Issue Invoice", use_container_width=True):
                with st.form("issue_inv_modal"):
                    st.markdown("**Issue New GST Invoice**")
                    s_date = st.date_input("Invoice Date", date.today())
                    s_inv = st.text_input("Invoice ID", f"INV-{len(sales_df)+101}")
                    s_plat = st.selectbox("Client / Platform", ["Meesho", "Amazon", "Flipkart", "Direct Customer"])
                    s_prod = st.text_input("Product Name", "Gold-Plated Jewellery Set")
                    s_sku = st.text_input("SKU", "GK-JW-01")
                    s_qty = st.number_input("Qty", min_value=1, value=1)
                    s_price = st.number_input("Unit Selling Price (Inclusive ₹)", min_value=1.0, value=249.0)
                    s_gst = st.selectbox("GST %", [3, 5, 12, 18], index=0)
                    if st.form_submit_button("✅ Save & Issue Invoice", type="primary"):
                        tot = s_qty * s_price
                        tx = round(tot / (1 + (s_gst / 100)), 2)
                        tax = round(tot - tx, 2)
                        new_s = pd.DataFrame([{"Date": str(s_date), "Invoice_No": s_inv, "Platform": s_plat, "Product_Name": s_prod, "SKU": s_sku, "Qty": s_qty, "Selling_Price": s_price, "GST_Rate": s_gst, "Taxable_Value": tx, "CGST": round(tax/2, 2), "SGST": round(tax/2, 2), "Total": tot}])
                        conn.update(worksheet="Sales", data=pd.concat([sales_df, new_s], ignore_index=True))
                        st.success("Invoice Issued!")
                        st.rerun()

    sub_tabs = st.tabs(["All Invoices", "Generator", "Upload Invoice", "Drafts", "Expenses", "Bills Manager"])
    with sub_tabs[0]:
        total_inv_count = len(sales_df)
        total_inv_amt = pd.to_numeric(sales_df["Total"], errors="coerce").sum() if not sales_df.empty else 0.0

        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: st.markdown(f'<div class="b-metric-card"><div style="color:#64748b; font-size:13px;">Total Invoices 📄</div><div style="font-size:26px; font-weight:800; margin:6px 0;">{total_inv_count}</div><div style="font-size:12px; color:#94a3b8;">All time invoices</div></div>', unsafe_allow_html=True)
        with mc2: st.markdown(f'<div class="b-metric-card"><div style="color:#64748b; font-size:13px;">Total Amount ₹</div><div style="font-size:26px; font-weight:800; margin:6px 0;">₹{total_inv_amt:,.0f}</div><div style="font-size:12px; color:#10b981;">+₹{total_inv_amt:,.0f} in last 30 days</div></div>', unsafe_allow_html=True)
        with mc3: st.markdown('<div class="b-metric-card"><div style="color:#64748b; font-size:13px;">Pending Invoices 🕒</div><div style="font-size:26px; font-weight:800; margin:6px 0;">0</div><div style="font-size:12px; color:#94a3b8;">Amount: ₹0</div></div>', unsafe_allow_html=True)
        with mc4: st.markdown('<div class="b-metric-card"><div style="color:#64748b; font-size:13px;">Overdue ❗</div><div style="font-size:26px; font-weight:800; margin:6px 0;">0</div><div style="font-size:12px; color:#ef4444;">Amount: ₹0</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        fl1, fl2, fl3, fl4, fl5 = st.columns([4, 1.5, 1.5, 1.5, 1.5])
        q_inv = fl1.text_input("🔍 Search by clients, invoice number", label_visibility="collapsed", placeholder="🔍 Search by clients, invoice number")
        fl2.selectbox("Status", ["Status: All", "Paid", "Pending"], label_visibility="collapsed")
        fl3.selectbox("Dates", ["All dates", "This Month", "Last 30 days"], label_visibility="collapsed")
        fl4.selectbox("Clients", ["All Clients", "Meesho", "Amazon", "Flipkart"], label_visibility="collapsed")
        fl5.selectbox("Amount", ["Amount: All", "High to Low"], label_visibility="collapsed")

        if sales_df.empty:
            st.markdown('<div class="empty-state-box">📄<br><b>No results found</b></div>', unsafe_allow_html=True)
        else:
            disp_s = sales_df[sales_df["Invoice_No"].astype(str).str.contains(q_inv, case=False, na=False) | sales_df["Platform"].astype(str).str.contains(q_inv, case=False, na=False)] if q_inv else sales_df
            st.dataframe(disp_s, use_container_width=True)

    with sub_tabs[1]:
        st.info("Use the '+ Issue Invoice' button on the top right to generate a GST invoice.")

# ==============================================================================
# PAGE 4: PURCHASES -> BILLS & OTHER EXPENSES (SCREENSHOT 4 EXACT REPLICA)
# ==============================================================================
elif current_page in ["Bills", "Other Expenses"]:
    bh1, bh2 = st.columns([5, 5])
    with bh1:
        st.caption("Bills Manager")
        st.markdown("## Bills & Expenses")
        st.caption("Track and manage your business expenses and vendor bills")
    with bh2:
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.download_button("📥 Export Report", purch_df.to_csv(index=False), "purchase_bills.csv", "text/csv", use_container_width=True)
        with b2:
            st.download_button("📘 Export GSTR-2", purch_df.to_csv(index=False), "gstr2_itc.csv", "text/csv", use_container_width=True)
        with b3:
            if st.button("📙 Export GSTR-3B", key="b_3b", use_container_width=True):
                st.session_state.page = "GSTR-3B Filing"
                st.rerun()
        with b4:
            with st.popover("➕ Add Bill", use_container_width=True):
                with st.form("add_bill_modal"):
                    st.markdown("**Add Vendor Purchase Bill (ITC)**")
                    p_date = st.date_input("Bill Date", date.today())
                    p_bill = st.text_input("Bill / Invoice ID", f"BILL-{len(purch_df)+101}")
                    p_supp = st.text_input("Vendor / Supplier Name", "Guwahati Wholesale Jewellery")
                    p_cat = st.selectbox("Category", ["Imitation Jewellery Stock", "Packaging Material", "Courier / Shipping", "Other Expense"])
                    p_tot = st.number_input("Total Bill Amount Paid (₹)", min_value=1.0, value=1500.0)
                    p_gst = st.selectbox("GST % on Bill", [3, 5, 12, 18], index=0)
                    if st.form_submit_button("✅ Save Vendor Bill", type="primary"):
                        tx = round(p_tot / (1 + (p_gst / 100)), 2)
                        itc = round(p_tot - tx, 2)
                        new_p = pd.DataFrame([{"Date": str(p_date), "Bill_No": p_bill, "Supplier_Name": p_supp, "Category": p_cat, "Total_Bill_Amount": p_tot, "GST_Rate": p_gst, "Taxable_Amount": tx, "ITC_Claimed": itc}])
                        conn.update(worksheet="Purchases", data=pd.concat([purch_df, new_p], ignore_index=True))
                        st.success("Vendor Bill Saved!")
                        st.rerun()

    b_tabs = st.tabs(["Bills Manager", "Expenses", "All Invoices", "Generator", "Upload Invoice", "Drafts"])
    with b_tabs[0]:
        tot_bills = len(purch_df)
        tot_paid = pd.to_numeric(purch_df["Total_Bill_Amount"], errors="coerce").sum() if not purch_df.empty else 0.0

        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1: st.markdown(f'<div class="b-metric-card"><div style="color:#64748b; font-size:13px;">Bills to Pay ❗</div><div style="font-size:26px; font-weight:800; margin:6px 0;">0</div><div style="font-size:12px; color:#94a3b8;">Pending vendor bills</div></div>', unsafe_allow_html=True)
        with mc2: st.markdown(f'<div class="b-metric-card"><div style="color:#64748b; font-size:13px;">Total Payable ₹</div><div style="font-size:26px; font-weight:800; margin:6px 0;">₹0</div><div style="font-size:12px; color:#94a3b8;">Due in next 30 days</div></div>', unsafe_allow_html=True)
        with mc3: st.markdown(f'<div class="b-metric-card"><div style="color:#64748b; font-size:13px;">Paid (Last 30d) ✔</div><div style="font-size:26px; font-weight:800; margin:6px 0;">₹{tot_paid:,.0f}</div><div style="font-size:12px; color:#10b981;">{tot_bills} bills recorded</div></div>', unsafe_allow_html=True)
        with mc4: st.markdown('<div class="b-metric-card"><div style="color:#64748b; font-size:13px;">Overdue ↻</div><div style="font-size:26px; font-weight:800; margin:6px 0;">₹0</div><div style="font-size:12px; color:#94a3b8;">Past due date</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns([5, 1.6, 1.6, 1.8])
        q_bill = s1.text_input("🔍 Search bills...", label_visibility="collapsed", placeholder="🔍 Search bills...")
        s2.selectbox("St", ["Status: All", "Paid", "Unpaid"], label_visibility="collapsed")
        s3.selectbox("Vn", ["Vendor", "All Vendors"], label_visibility="collapsed")
        s4.selectbox("Dt", ["Bill date: All dates", "This Month"], label_visibility="collapsed")

        if purch_df.empty:
            st.markdown('<div class="empty-state-box">🧾<br><b>No results found</b></div>', unsafe_allow_html=True)
        else:
            disp_p = purch_df[purch_df["Supplier_Name"].astype(str).str.contains(q_bill, case=False, na=False) | purch_df["Bill_No"].astype(str).str.contains(q_bill, case=False, na=False)] if q_bill else purch_df
            st.dataframe(disp_p, use_container_width=True)

# ==============================================================================
# PAGE 5: KHATA BOOK (SCREENSHOT 5 & 6 EXACT REPLICA)
# ==============================================================================
elif current_page == "Khata Book":
    kh1, kh2 = st.columns([8, 2])
    with kh1:
        st.markdown("### 📖 Khata Book")
        st.caption("Track credit and payments with customers")
    with kh2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    t_c1, t_c2, _ = st.columns([1.5, 1.5, 7])
    if t_c1.button("👥 Customers", type="primary" if st.session_state.khata_mode == "Customers" else "secondary", use_container_width=True):
        st.session_state.khata_mode = "Customers"
        st.rerun()
    if t_c2.button("🏪 Vendors", type="primary" if st.session_state.khata_mode == "Vendors" else "secondary", use_container_width=True):
        st.session_state.khata_mode = "Vendors"
        st.rerun()

    party_df = pd.DataFrame(st.session_state.parties_list)
    sub_p = party_df[party_df["Type"] == ("Customer" if st.session_state.khata_mode == "Customers" else "Vendor")] if not party_df.empty else pd.DataFrame()
    tot_out = sub_p["Balance"].sum() if not sub_p.empty else 0.0
    cust_cnt = len(sub_p[sub_p["Balance"] > 0]) if not sub_p.empty else 0

    km1, km2, km3, km4 = st.columns(4)
    with km1: st.markdown(f'<div class="b-metric-card"><div style="display:flex; justify-content:space-between;"><span style="color:#10b981; font-weight:700;">📈</span><span style="background:#dcfce7; color:#15803d; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px;">To Receive</span></div><div style="font-size:26px; font-weight:800; margin-top:10px;">₹{tot_out:,.0f}</div><div style="font-size:12px; color:#64748b;">Outstanding from {st.session_state.khata_mode.lower()}</div></div>', unsafe_allow_html=True)
    with km2: st.markdown('<div class="b-metric-card"><div style="display:flex; justify-content:space-between;"><span>❗</span><span style="background:#fee2e2; color:#b91c1c; font-size:10px; font-weight:700; padding:2px 8px; border-radius:10px;">0 overdue</span></div><div style="font-size:26px; font-weight:800; margin-top:10px;">₹0</div><div style="font-size:12px; color:#64748b;">Past due date</div></div>', unsafe_allow_html=True)
    with km3: st.markdown(f'<div class="b-metric-card"><span style="color:#4f46e5; font-weight:700;">₹</span><div style="font-size:26px; font-weight:800; margin-top:10px;">₹{tot_out:,.0f}</div><div style="font-size:12px; color:#64748b;">Net Balance</div></div>', unsafe_allow_html=True)
    with km4: st.markdown(f'<div class="b-metric-card"><span style="color:#6366f1;">👥</span><div style="font-size:26px; font-weight:800; margin-top:10px;">{cust_cnt}</div><div style="font-size:12px; color:#64748b;">{st.session_state.khata_mode} with balance</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    kl, kr = st.columns([6.5, 3.5])
    with kl:
        st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
        sc1, sc2 = st.columns([5, 5])
        sc1.markdown(f"#### {st.session_state.khata_mode}")
        q_k = sc2.text_input("Search", placeholder=f"🔍 Search {st.session_state.khata_mode.lower()}...", label_visibility="collapsed")

        st.markdown("""
        <div style="padding: 18px 10px;">
            <div style="font-size:16px; font-weight:700; color:#0f172a;">Khata Book — Credit tracking simplified.</div>
            <div style="font-size:12.5px; color:#64748b; margin:6px 0 14px 0;">Track credit given to customers and payments received, all in one place.</div>
            <div style="font-size:12.5px; color:#475569; margin-bottom:4px;">✔ Track credit given and payments received</div>
            <div style="font-size:12.5px; color:#475569; margin-bottom:4px;">✔ Send payment reminders to customers</div>
            <div style="font-size:12.5px; color:#475569; margin-bottom:14px;">✔ Convert credits to invoices automatically</div>
        </div>
        """, unsafe_allow_html=True)

        with st.popover(f"➕ Add your first {st.session_state.khata_mode[:-1]}"):
            with st.form("khata_add_form"):
                k_name = st.text_input("Name *")
                k_phone = st.text_input("Mobile Number")
                k_bal = st.number_input("Opening Credit Balance (₹)", value=0.0, step=100.0)
                if st.form_submit_button("Save Entry", type="primary"):
                    st.session_state.parties_list.append({"Name": k_name, "Type": st.session_state.khata_mode[:-1], "Phone": k_phone, "GSTIN": "Unregistered", "Balance": k_bal, "Due_Date": str(date.today())})
                    st.rerun()

        if not sub_p.empty:
            st.dataframe(sub_p, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with kr:
        st.markdown('<div class="b-section-box"><div style="font-weight:700;">📉 Top Outstanding</div><div style="font-size:12.5px; color:#94a3b8; text-align:center; padding:25px 0;">No outstanding balances</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="b-section-box"><div style="font-weight:700;">🕒 Recent Transactions</div><div style="font-size:12.5px; color:#94a3b8; text-align:center; padding:25px 0;">No recent transactions</div></div>', unsafe_allow_html=True)

# ==============================================================================
# PAGE 6: DASHBOARD (MAIN OVERVIEW)
# ==============================================================================
elif current_page == "Dashboard":
    st.markdown("## 📊 Business Overview & GST Dashboard")
    total_sales = pd.to_numeric(sales_df["Total"], errors='coerce').sum() if not sales_df.empty else 0.0
    total_purchases = pd.to_numeric(purch_df["Total_Bill_Amount"], errors='coerce').sum() if not purch_df.empty else 0.0
    output_gst = (pd.to_numeric(sales_df["CGST"], errors='coerce').sum() + pd.to_numeric(sales_df["SGST"], errors='coerce').sum()) if not sales_df.empty else 0.0
    input_itc = pd.to_numeric(purch_df["ITC_Claimed"], errors='coerce').sum() if not purch_df.empty else 0.0

    d1, d2, d3, d4 = st.columns(4)
    with d1: st.markdown(f'<div class="b-metric-card"><div style="color:#64748b; font-size:12px; font-weight:700;">TOTAL SALES (BIKRI)</div><div style="font-size:28px; font-weight:800; margin:8px 0;">₹{total_sales:,.0f}</div><div style="color:#10b981; font-size:12px;">Meesho / Amazon / Flipkart</div></div>', unsafe_allow_html=True)
    with d2: st.markdown(f'<div class="b-metric-card"><div style="color:#64748b; font-size:12px; font-weight:700;">WHOLESALE & PACKING</div><div style="font-size:28px; font-weight:800; margin:8px 0;">₹{total_purchases:,.0f}</div><div style="color:#64748b; font-size:12px;">Total Vendor Bills</div></div>', unsafe_allow_html=True)
    with d3: st.markdown(f'<div class="b-metric-card"><div style="color:#64748b; font-size:12px; font-weight:700;">NET CASH FLOW</div><div style="font-size:28px; font-weight:800; margin:8px 0;">₹{(total_sales - total_purchases):,.0f}</div><div style="color:#64748b; font-size:12px;">Sales minus Purchases</div></div>', unsafe_allow_html=True)
    with d4: st.markdown(f'<div class="b-metric-card" style="background:#0f172a; color:white;"><div style="color:#facc15; font-size:12px; font-weight:700;">NET ITC / GST BALANCE</div><div style="font-size:28px; font-weight:800; margin:8px 0;">₹{(input_itc - output_gst):,.2f}</div><div style="color:#94a3b8; font-size:12px;">Eligible ITC minus Output GST</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns(2)
    with cl:
        st.markdown('<div class="b-section-box"><b>Recent Sales Invoices</b>', unsafe_allow_html=True)
        st.dataframe(sales_df.tail(8), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with cr:
        st.markdown('<div class="b-section-box"><b>Recent Vendor Purchase Bills (ITC)</b>', unsafe_allow_html=True)
        st.dataframe(purch_df.tail(8), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# PAGE 7: PRICING (MARKETPLACE PRICE CALCULATOR & PLAN INFO)
# ==============================================================================
elif current_page == "Pricing":
    st.markdown("## 👑 Pricing & Product Margin Calculator")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
        sku = st.text_input("SKU Code", "GK-BR-001")
        prod_name = st.text_input("Product Name", "GK Collection Gold-Plated Bracelet")
        buy_cost = st.number_input("Wholesale Buy Cost (₹)", value=50.0)
        pack_cost = st.number_input("Packaging Cost (₹)", value=10.0)
        ship_fee = st.number_input("Shipping / Platform Fee (₹)", value=55.0)
        profit = st.number_input("Target Net Profit (₹)", value=50.0)
        gst_slab = st.selectbox("GST %", [3, 5, 12, 18], index=0)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        sp = round(buy_cost + pack_cost + ship_fee + profit)
        mrp = max(sp * 2, 299)
        tx = round(sp / (1 + (gst_slab / 100)), 2)
        st.markdown(f"""
        <div class="b-section-box">
            <div style="font-size:12px; font-weight:700; color:#4f46e5;">CALCULATED MEESHO / AMAZON SELLING PRICE</div>
            <div style="font-size:34px; font-weight:800; margin:10px 0;">₹{sp} <span style="font-size:14px; color:#10b981;">(GST Inclusive)</span></div>
            <p><b>Suggested MRP:</b> ₹{mrp} | <b>Taxable Value:</b> ₹{tx} | <b>GST ({gst_slab}%):</b> ₹{round(sp-tx, 2)}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💾 Save Product to Google Sheet Catalog", type="primary"):
            new_c = pd.DataFrame([{"SKU": sku, "Product_Name": prod_name, "Buy_Cost": buy_cost, "Packaging_Cost": pack_cost, "Platform_Fee": ship_fee, "Profit_Margin": profit, "Selling_Price": sp, "Suggested_MRP": mrp, "GST_Rate": gst_slab, "Net_Weight_g": 50}])
            conn.update(worksheet="Catalog", data=pd.concat([cat_df, new_c], ignore_index=True))
            st.success("Saved to Catalog!")
            st.rerun()
    st.dataframe(cat_df, use_container_width=True)

# ==============================================================================
# PAGE 8: REMAINING SIDEBAR PAGES (SAVED REPORTS, PARTIES, CONNECTIONS, CHAT, SETTINGS)
# ==============================================================================
elif current_page == "Saved Reports":
    st.markdown("## 🗂️ Saved GST Reports")
    if not st.session_state.saved_reports:
        st.markdown('<div class="empty-state-box">No saved reports yet. Click Analyze on GSTR-1 to save a report snapshot.</div>', unsafe_allow_html=True)
    else:
        st.dataframe(pd.DataFrame(st.session_state.saved_reports)[["Type", "Period", "Generated_On"]], use_container_width=True)

elif current_page == "Parties":
    st.markdown("## 👥 Parties (Customers & Vendors Directory)")
    st.dataframe(pd.DataFrame(st.session_state.parties_list), use_container_width=True)

elif current_page == "Connections":
    st.markdown("## 🤝 Marketplace & Database Connections")
    st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
    st.checkbox("✅ Google Sheets Live Database (`GK_Collection_DB`)", value=True)
    st.checkbox("✅ Meesho Supplier B2C Excel/CSV Parser", value=True)
    st.checkbox("✅ Amazon Seller Central MTR B2C Parser", value=True)
    st.checkbox("✅ Flipkart Seller Hub Tax Report Parser", value=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "Chat":
    st.markdown("## 💬 Billoora AI Tax & E-Commerce Assistant")
    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["text"])
    q = st.chat_input("Ask about GSTR-1 JSON, HSN codes, or Meesho TCS claims...")
    if q:
        st.session_state.chat_history.append({"role": "user", "text": q})
        reply = "Jewellery (Imitation) par 3% GST lagta hai (HSN 7117). Aap GSTR-1 Filing page mein Meesho ki tcs_sales.xlsx upload karke seedha GST Portal ka JSON download kar sakte hain."
        st.session_state.chat_history.append({"role": "assistant", "text": reply})
        st.rerun()

elif current_page in ["Reports", "Billing", "Revenue - Sources", "Revenue - Reports", "Revenue - AI Summary"]:
    st.markdown(f"## 📈 {current_page}")
    st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
    st.write("**Channel-Wise Revenue & Tax Breakdown**")
    st.dataframe(sales_df, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "Settings":
    st.markdown("## ⚙️ Business & GST Settings")
    st.markdown('<div class="b-section-box">', unsafe_allow_html=True)
    st.session_state.biz_name = st.text_input("Legal / Trade Business Name", value=st.session_state.biz_name)
    st.session_state.user_gstin = st.text_input("Registered GSTIN (Assam - 18)", value=st.session_state.user_gstin)
    st.text_input("Principal Place of Business (GST Registered)", value="Permanent Home Address, Assam")
    st.text_input("Additional Place of Business (Courier Pickup)", value="Rented Dispatch Hub, Guwahati, Assam")
    if st.button("Save Settings", type="primary"):
        st.success("Business profile updated across all GST returns!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
