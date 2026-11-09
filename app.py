import streamlit as st
import pandas as pd
import json
import io
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="GK Collection — Billoora Business Suite", page_icon="💎", layout="wide")

# Custom CSS matching Billoora UI
st.markdown("""
<style>
.stApp { background-color: #f8fafc; color: #0f172a; }
.top-banner {
    background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
    padding: 16px 26px;
    border-radius: 14px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
}
.brand-box { display: flex; align-items: center; gap: 14px; }
.logo-icon {
    background: #6d28d9;
    color: white;
    font-weight: 800;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 18px;
}
.b-card {
    background: #ffffff;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    margin-bottom: 16px;
}
.b-card-active {
    background: #ffffff;
    padding: 20px;
    border-radius: 14px;
    border: 2px solid #10b981;
    box-shadow: 0 4px 12px rgba(16,185,129,0.08);
    margin-bottom: 16px;
}
.b-card-dark {
    background: #0f172a;
    padding: 20px;
    border-radius: 14px;
    color: #ffffff;
    margin-bottom: 16px;
}
.gstr2b-box {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    padding: 18px;
    border-radius: 14px;
    margin-bottom: 20px;
}
.badge-b2c {
    background: #ede9fe;
    color: #5b21b6;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 10px;
}
.c-title { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.c-val { font-size: 28px; font-weight: 800; color: #0f172a; margin: 6px 0; }
.c-sub { font-size: 12px; color: #64748b; }
.plat-row { margin-bottom: 14px; }
.plat-label { display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; margin-bottom: 5px; }
.bar-bg { width: 100%; background: #f1f5f9; height: 10px; border-radius: 8px; overflow: hidden; }
</style>
<div class="top-banner">
<div class="brand-box">
<div class="logo-icon">GK</div>
<div>
<div style="font-size: 19px; font-weight: 700;">GK Collection — Billoora Business Suite</div>
<div style="font-size: 12px; color: #94a3b8;">GSTR-1 & GSTR-3B JSON Filing • E-Commerce Accounting</div>
</div>
</div>
<div style="font-size: 13px; color: #cbd5e1;">Assam (State Code: 18)</div>
</div>
""", unsafe_allow_html=True)

# Google Sheets Connection
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet_name, columns):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=5)
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df.dropna(how="all")
    except Exception:
        return pd.DataFrame(columns=columns)

sales_cols = ["Date", "Invoice_No", "Platform", "Product_Name", "SKU", "Qty", "Selling_Price", "GST_Rate", "Taxable_Value", "CGST", "SGST", "Total"]
purch_cols = ["Date", "Bill_No", "Supplier_Name", "Category", "Total_Bill_Amount", "GST_Rate", "Taxable_Amount", "ITC_Claimed"]
cat_cols = ["SKU", "Product_Name", "Buy_Cost", "Packaging_Cost", "Platform_Fee", "Profit_Margin", "Selling_Price", "Suggested_MRP", "GST_Rate", "Net_Weight_g"]

sales_df = load_data("Sales", sales_cols)
purch_df = load_data("Purchases", purch_cols)
cat_df = load_data("Catalog", cat_cols)

# Helper: Universal Marketplace File Parser (Meesho, Flipkart, Amazon, Manual)
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
        else:
            return pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"File padhne mein error ({uploaded_file.name}): {e}")
        return pd.DataFrame()

def standardize_b2c_df(df, source_name, sign=1):
    if df.empty:
        return pd.DataFrame(columns=["Source", "POS", "GST_Rate", "Taxable_Value"])
    
    cols = {str(c).lower().strip(): c for c in df.columns}
    
    # Detect State / POS column
    state_col = next((cols[k] for k in cols if any(w in k for w in ["end_customer_state", "customer_state", "ship to state", "destination state", "pos", "state", "place of supply"])), None)
    # Detect Taxable Value column
    tax_col = next((cols[k] for k in cols if any(w in k for w in ["taxable", "net_taxable", "taxable_value", "taxable amount", "principal", "basic"])), None)
    # Detect GST Rate column
    rate_col = next((cols[k] for k in cols if any(w in k for w in ["gst_rate", "tax_rate", "igst_rate", "rate", "gst %", "gst_pct"])), None)

    out = pd.DataFrame()
    if tax_col:
        out["Taxable_Value"] = pd.to_numeric(df[tax_col], errors="coerce").fillna(0.0) * sign
    else:
        amt_col = next((cols[k] for k in cols if any(w in k for w in ["total", "invoice_value", "selling_price", "amount"])), None)
        if amt_col:
            out["Taxable_Value"] = (pd.to_numeric(df[amt_col], errors="coerce").fillna(0.0) / 1.03) * sign
        else:
            out["Taxable_Value"] = 0.0

    if rate_col:
        r_vals = pd.to_numeric(df[rate_col], errors="coerce").fillna(3.0)
        # If decimal rate like 0.03, convert to 3
        r_vals = r_vals.apply(lambda x: round(x * 100, 1) if 0 < x < 1 else x)
        out["GST_Rate"] = r_vals
    else:
        out["GST_Rate"] = 3.0

    if state_col:
        raw_state = df[state_col].astype(str).str.upper().str.strip()
        def map_pos(val):
            for s_name, s_code in STATE_MAP.items():
                if s_name in val or val.startswith(s_code):
                    return s_code
            return "18"
        out["POS"] = raw_state.apply(map_pos)
    else:
        out["POS"] = "18"

    out["Source"] = source_name
    return out[["Source", "POS", "GST_Rate", "Taxable_Value"]]

# Sidebar Settings & Navigation
with st.sidebar:
    st.markdown("### 🏢 Business Profile")
    user_gstin = st.text_input("Your GSTIN (Assam - 18)", value="18AAAAA0000A1Z5")
    home_state_code = user_gstin[:2] if len(user_gstin) >= 2 and user_gstin[:2].isdigit() else "18"
    
    st.divider()
    nav = st.radio(
        "BILLOORA MENU",
        [
            "📊 Dashboard",
            "📄 GSTR-1 Filing",
            "📑 GSTR-3B Filing",
            "🏷️ Pricing Calculator",
            "🧾 Sales & Invoices",
            "📦 Purchases (ITC)"
        ]
    )

# ==========================================
# 1. DASHBOARD
# ==========================================
if nav == "📊 Dashboard":
    st.subheader("Business Overview & GST Ledger")
    total_sales = pd.to_numeric(sales_df["Total"], errors='coerce').sum() if not sales_df.empty else 0.0
    total_purchases = pd.to_numeric(purch_df["Total_Bill_Amount"], errors='coerce').sum() if not purch_df.empty else 0.0
    net_cash = total_sales - total_purchases
    output_gst = (pd.to_numeric(sales_df["CGST"], errors='coerce').sum() + pd.to_numeric(sales_df["SGST"], errors='coerce').sum()) if not sales_df.empty else 0.0
    input_itc = pd.to_numeric(purch_df["ITC_Claimed"], errors='coerce').sum() if not purch_df.empty else 0.0
    itc_balance = input_itc - output_gst

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="b-card"><div class="c-title">TOTAL SALES 📈</div><div class="c-val">₹{total_sales:,.0f}</div><div class="c-sub">Meesho / Amazon / Flipkart</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="b-card"><div class="c-title">WHOLESALE PURCHASES 🛒</div><div class="c-val">₹{total_purchases:,.0f}</div><div class="c-sub">Stock + Packaging Bills</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="b-card"><div class="c-title">NET CASH FLOW 👛</div><div class="c-val">₹{net_cash:,.0f}</div><div class="c-sub">Sales minus Purchases</div></div>""", unsafe_allow_html=True)
    with c4:
        lbl = f"₹{itc_balance:,.2f} ITC" if itc_balance >= 0 else f"₹{abs(itc_balance):,.2f} Due"
        st.markdown(f"""<div class="b-card-dark"><div class="c-title" style="color:#facc15;">GST LEDGER 🛡️</div><div class="c-val" style="color:#fff;">{lbl}</div><div class="c-sub" style="color:#94a3b8;">Output GST: ₹{output_gst:,.2f}</div></div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**Recent Orders / Sales**")
        st.dataframe(sales_df.tail(8), use_container_width=True)
    with col_r:
        st.write("**Recent Wholesale Bills (ITC)**")
        st.dataframe(purch_df.tail(8), use_container_width=True)

# ==========================================
# 2. GSTR-1 FILING (EXACT BILLOORA REPLICA)
# ==========================================
elif nav == "📄 GSTR-1 Filing":
    st.markdown("## 📄 GSTR-1 Filing")
    st.caption("Combine sales from Meesho, Flipkart, Amazon, your Billoora invoices, and manual uploads into a single GSTR-1 return. Select one or more platforms below.")

    # Top Period Bar
    p1, p2, p3 = st.columns(3)
    filing_type = p1.selectbox("Type of Filing *", ["Monthly", "Quarterly"])
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    sel_month = p2.selectbox("Month *", months_list, index=9)
    sel_year = p3.selectbox("Year *", ["2026", "2025", "2027"], index=0)

    month_num = str(months_list.index(sel_month) + 1).zfill(2)
    fp_code = f"{month_num}{sel_year}"

    st.markdown("#### Platforms")
    col_m, col_f, col_a, col_b, col_man = st.columns(5)

    with col_m:
        st.markdown("""<div class="b-card-active"><span class="badge-b2c">B2C • MONTHLY</span><div style="font-weight:700; font-size:16px;">🛍️ Meesho</div><div class="c-sub">From Meesho Supplier Panel → Payments → Tax Invoices & Reports</div></div>""", unsafe_allow_html=True)
        m_sales_file = st.file_uploader("Upload tcs_sales.xlsx / csv", type=["xlsx", "csv"], key="g1_m_sales")
        m_ret_file = st.file_uploader("Upload tcs_sales_return.xlsx (Optional)", type=["xlsx", "csv"], key="g1_m_ret")

    with col_f:
        st.markdown("""<div class="b-card"><span class="badge-b2c">B2C • MONTHLY</span><div style="font-weight:700; font-size:16px;">🛒 Flipkart</div><div class="c-sub">From Flipkart Seller Hub → Reports → Sales Report</div></div>""", unsafe_allow_html=True)
        f_sales_file = st.file_uploader("Upload Flipkart Sales (.xlsx/.csv)", type=["xlsx", "csv"], key="g1_f_sales")

    with col_a:
        st.markdown("""<div class="b-card"><span class="badge-b2c">B2C • MONTHLY</span><div style="font-weight:700; font-size:16px;">📦 Amazon</div><div class="c-sub">From Amazon Seller Central → Reports → MTR B2C Report</div></div>""", unsafe_allow_html=True)
        a_sales_file = st.file_uploader("Upload Amazon MTR B2C (.csv/.xlsx)", type=["xlsx", "csv"], key="g1_a_sales")

    with col_b:
        st.markdown("""<div class="b-card"><span class="badge-b2c">Invoices • MONTHLY</span><div style="font-weight:700; font-size:16px;">🏢 Billoora DB</div><div class="c-sub">Include sales invoices saved in your Google Sheet DB</div></div>""", unsafe_allow_html=True)
        inc_billoora = st.checkbox("Include Sheet Sales", value=True, key="g1_inc_db")

    with col_man:
        st.markdown("""<div class="b-card"><span class="badge-b2c">Upload • MONTHLY</span><div style="font-weight:700; font-size:16px;">📄 Manual</div><div class="c-sub">Upload an Excel/CSV of offline or direct sales</div></div>""", unsafe_allow_html=True)
        man_file = st.file_uploader("Upload Manual Excel/CSV", type=["xlsx", "csv"], key="g1_man")

    analyze_btn = st.button("🔍 Analyze & Generate GSTR-1 Return", type="primary", use_container_width=True)

    if analyze_btn or m_sales_file or f_sales_file or a_sales_file or man_file or inc_billoora:
        dfs = []
        if m_sales_file:
            dfs.append(standardize_b2c_df(read_uploaded_file(m_sales_file), "Meesho", sign=1))
        if m_ret_file:
            dfs.append(standardize_b2c_df(read_uploaded_file(m_ret_file), "Meesho Return", sign=-1))
        if f_sales_file:
            dfs.append(standardize_b2c_df(read_uploaded_file(f_sales_file), "Flipkart", sign=1))
        if a_sales_file:
            dfs.append(standardize_b2c_df(read_uploaded_file(a_sales_file), "Amazon", sign=1))
        if man_file:
            dfs.append(standardize_b2c_df(read_uploaded_file(man_file), "Manual", sign=1))
        if inc_billoora and not sales_df.empty:
            db_temp = pd.DataFrame()
            db_temp["Source"] = "Billoora Sheet"
            db_temp["POS"] = home_state_code
            db_temp["GST_Rate"] = pd.to_numeric(sales_df["GST_Rate"], errors="coerce").fillna(3.0)
            db_temp["Taxable_Value"] = pd.to_numeric(sales_df["Taxable_Value"], errors="coerce").fillna(0.0)
            dfs.append(db_temp)

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
            grouped = combined.groupby(["POS", "GST_Rate"], as_index=False)["Taxable_Value"].sum()
            grouped["Taxable_Value"] = grouped["Taxable_Value"].round(2)

            b2cs_entries = []
            summary_rows = []

            for _, row in grouped.iterrows():
                pos = str(row["POS"]).zfill(2)
                rt = float(row["GST_Rate"])
                txval = round(float(row["Taxable_Value"]), 2)
                if txval == 0:
                    continue

                is_intra = (pos == home_state_code)
                sply_ty = "INTRA" if is_intra else "INTER"
                if is_intra:
                    camt = round(txval * (rt / 200.0), 2)
                    samt = round(txval * (rt / 200.0), 2)
                    iamt = 0.0
                    entry = {"sply_ty": "INTRA", "pos": pos, "typ": "OE", "txval": txval, "rt": rt, "camt": camt, "samt": samt, "csamt": 0.0}
                else:
                    iamt = round(txval * (rt / 100.0), 2)
                    camt = 0.0
                    samt = 0.0
                    entry = {"sply_ty": "INTER", "pos": pos, "typ": "OE", "txval": txval, "rt": rt, "iamt": iamt, "csamt": 0.0}

                b2cs_entries.append(entry)
                summary_rows.append({
                    "Place of Supply (POS)": pos,
                    "Supply Type": sply_ty,
                    "GST Rate (%)": rt,
                    "Taxable Value (₹)": txval,
                    "IGST (₹)": iamt,
                    "CGST (₹)": camt,
                    "SGST (₹)": samt,
                    "Total Tax (₹)": round(iamt + camt + samt, 2)
                })

            sum_df = pd.DataFrame(summary_rows)
            st.divider()
            st.markdown(f"### 📊 GSTR-1 B2CS Summary (Period: {sel_month} {sel_year})")

            if not sum_df.empty:
                st.dataframe(sum_df, use_container_width=True)

                tot_txval = round(sum_df["Taxable_Value (₹)"].sum(), 2) if "Taxable_Value (₹)" in sum_df else round(sum_df["Taxable Value (₹)"].sum(), 2)
                tot_igst = round(sum_df["IGST (₹)"].sum(), 2)
                tot_cgst = round(sum_df["CGST (₹)"].sum(), 2)
                tot_sgst = round(sum_df["SGST (₹)"].sum(), 2)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Taxable Turnover", f"₹{tot_txval:,.2f}")
                m2.metric("Total IGST", f"₹{tot_igst:,.2f}")
                m3.metric("Total CGST", f"₹{tot_cgst:,.2f}")
                m4.metric("Total SGST", f"₹{tot_sgst:,.2f}")

                # Official GST Portal GSTR-1 JSON Structure
                gstr1_json_data = {
                    "gstin": user_gstin,
                    "fp": fp_code,
                    "version": "GST3.1.6",
                    "hash": "hash",
                    "b2cs": b2cs_entries
                }
                json_str = json.dumps(gstr1_json_data, indent=2)

                # Excel Buffer
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                    sum_df.to_excel(writer, index=False, sheet_name="GSTR1_B2CS_Summary")
                    combined.to_excel(writer, index=False, sheet_name="Raw_Combined_Sources")

                b_col1, b_col2, b_col3 = st.columns(3)
                with b_col1:
                    with st.expander("📋 Copy Totals"):
                        st.code(f"Taxable: {tot_txval}\nIGST: {tot_igst}\nCGST: {tot_cgst}\nSGST: {tot_sgst}")
                with b_col2:
                    st.download_button(
                        label="📥 Download Excel Summary",
                        data=excel_buf.getvalue(),
                        file_name=f"GSTR1_{user_gstin}_{fp_code}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with b_col3:
                    st.download_button(
                        label="⬇️ Download JSON (for GST portal)",
                        data=json_str,
                        file_name=f"GSTR1_{user_gstin}_{fp_code}.json",
                        mime="application/json",
                        type="primary",
                        use_container_width=True
                    )
            else:
                st.info("Uploaded files ya sheet mein abhi koi valid B2C sales data nahi mila.")

# ==========================================
# 3. GSTR-3B FILING (EXACT BILLOORA REPLICA)
# ==========================================
elif nav == "📑 GSTR-3B Filing":
    st.markdown("## 📑 GSTR-3B Filing")
    st.caption("Outward supplies (Table 3.1/3.2) are computed from your Meesho/Amazon/Flipkart/Billoora sources. Eligible ITC (Table 4) comes from your GSTR-2B JSON or Purchase register.")

    p1, p2, p3 = st.columns(3)
    filing_type_3b = p1.selectbox("Type of Filing *", ["Monthly", "Quarterly"], key="3b_type")
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    sel_month_3b = p2.selectbox("Month *", months_list, index=9, key="3b_m")
    sel_year_3b = p3.selectbox("Year *", ["2026", "2025", "2027"], index=0, key="3b_y")
    fp_3b = f"{str(months_list.index(sel_month_3b) + 1).zfill(2)}{sel_year_3b}"

    st.markdown("""<div class="gstr2b-box"><div style="font-weight:700; color:#166534; margin-bottom:4px;">GSTR-2B (ITC source) *</div><div style="font-size:12px; color:#15803d;">Download from GST Portal → Services → Returns → GSTR-2B → Download JSON</div></div>""", unsafe_allow_html=True)
    gstr2b_file = st.file_uploader("Choose GSTR-2B .json file (Optional - Auto-fills ITC)", type=["json"], key="3b_2b")

    st.markdown("#### Outward Supply Sources")
    use_meesho = st.checkbox("Meesho / Marketplace e-commerce sales", value=True)
    if use_meesho:
        mc1, mc2, mc3 = st.columns(3)
        tcs_sales_3b = mc1.file_uploader("TCS Sales Report (tcs_sales.xlsx)", type=["xlsx", "csv"], key="3b_ms")
        tcs_ret_3b = mc2.file_uploader("TCS Sales Return (tcs_sales_return.xlsx)", type=["xlsx", "csv"], key="3b_mr")
        tax_inv_3b = mc3.file_uploader("Amazon / Flipkart Sales Report (Optional)", type=["xlsx", "csv"], key="3b_af")
    else:
        tcs_sales_3b, tcs_ret_3b, tax_inv_3b = None, None, None

    use_billoora_3b = st.checkbox("Billoora invoices (my own Google Sheet sales)", value=True)
    use_purch_itc = st.checkbox("Include Wholesale Purchase Register ITC (from Google Sheets)", value=True)

    # Compute Outward Supplies (Table 3.1a)
    out_dfs = []
    if tcs_sales_3b:
        out_dfs.append(standardize_b2c_df(read_uploaded_file(tcs_sales_3b), "Meesho", 1))
    if tcs_ret_3b:
        out_dfs.append(standardize_b2c_df(read_uploaded_file(tcs_ret_3b), "Meesho Return", -1))
    if tax_inv_3b:
        out_dfs.append(standardize_b2c_df(read_uploaded_file(tax_inv_3b), "Other Marketplace", 1))
    if use_billoora_3b and not sales_df.empty:
        db_s = pd.DataFrame()
        db_s["Source"] = "Sheet"
        db_s["POS"] = home_state_code
        db_s["GST_Rate"] = pd.to_numeric(sales_df["GST_Rate"], errors="coerce").fillna(3.0)
        db_s["Taxable_Value"] = pd.to_numeric(sales_df["Taxable_Value"], errors="coerce").fillna(0.0)
        out_dfs.append(db_s)

    tot_out_taxable, tot_out_igst, tot_out_cgst, tot_out_sgst = 0.0, 0.0, 0.0, 0.0
    if out_dfs:
        comb_3b = pd.concat(out_dfs, ignore_index=True)
        for _, r in comb_3b.iterrows():
            pos = str(r["POS"]).zfill(2)
            rt = float(r["GST_Rate"])
            tx = float(r["Taxable_Value"])
            tot_out_taxable += tx
            if pos == home_state_code:
                tot_out_cgst += tx * (rt / 200.0)
                tot_out_sgst += tx * (rt / 200.0)
            else:
                tot_out_igst += tx * (rt / 100.0)

    # Compute Eligible ITC (Table 4)
    itc_igst, itc_cgst, itc_sgst = 0.0, 0.0, 0.0
    if gstr2b_file:
        try:
            g2b_json = json.load(gstr2b_file)
            docdata = g2b_json.get("data", {}).get("cpsumm", {}).get("b2b", [])
            for sup in docdata:
                itc_igst += float(sup.get("iamt", 0.0))
                itc_cgst += float(sup.get("camt", 0.0))
                itc_sgst += float(sup.get("samt", 0.0))
        except Exception:
            st.warning("GSTR-2B JSON structure custom hai, Sheet ITC use kiya ja raha hai.")

    if use_purch_itc and not purch_df.empty:
        sheet_itc = pd.to_numeric(purch_df["ITC_Claimed"], errors="coerce").sum()
        itc_cgst += sheet_itc / 2.0
        itc_sgst += sheet_itc / 2.0

    st.divider()
    st.markdown("### 📊 GSTR-3B Auto-Computed Tables")
    c31, c4 = st.columns(2)
    with c31:
        st.write("**Table 3.1(a): Outward Taxable Supplies**")
        t31_df = pd.DataFrame([{
            "Taxable Value (₹)": round(tot_out_taxable, 2),
            "IGST (₹)": round(tot_out_igst, 2),
            "CGST (₹)": round(tot_out_cgst, 2),
            "SGST (₹)": round(tot_out_sgst, 2)
        }])
        st.dataframe(t31_df, use_container_width=True)

    with c4:
        st.write("**Table 4(A)(5): Eligible Input Tax Credit (ITC)**")
        t4_df = pd.DataFrame([{
            "IGST ITC (₹)": round(itc_igst, 2),
            "CGST ITC (₹)": round(itc_cgst, 2),
            "SGST ITC (₹)": round(itc_sgst, 2),
            "Total ITC (₹)": round(itc_igst + itc_cgst + itc_sgst, 2)
        }])
        st.dataframe(t4_df, use_container_width=True)

    gstr3b_json = {
        "gstin": user_gstin,
        "ret_period": fp_3b,
        "sup_details": {
            "osup_det": {
                "txval": round(tot_out_taxable, 2),
                "iamt": round(tot_out_igst, 2),
                "camt": round(tot_out_cgst, 2),
                "samt": round(tot_out_sgst, 2),
                "csamt": 0.0
            }
        },
        "itc_elg": {
            "itc_avl": [
                {
                    "ty": "OTH",
                    "iamt": round(itc_igst, 2),
                    "camt": round(itc_cgst, 2),
                    "samt": round(itc_sgst, 2),
                    "csamt": 0.0
                }
            ]
        }
    }

    st.download_button(
        label="⬇️ Download GSTR-3B JSON (for GST Portal)",
        data=json.dumps(gstr3b_json, indent=2),
        file_name=f"GSTR3B_{user_gstin}_{fp_3b}.json",
        mime="application/json",
        type="primary",
        use_container_width=True
    )

# ==========================================
# 4. PRICING CALCULATOR
# ==========================================
elif nav == "🏷️ Pricing Calculator":
    st.subheader("Meesho / Amazon Listing Price & MRP Calculator")
    c1, c2 = st.columns(2)
    with c1:
        sku = st.text_input("SKU Code", "GK-BR-001")
        prod_name = st.text_input("Product Title", "GK Collection Gold-Plated Bracelet")
        buy_cost = st.number_input("Wholesale Buy Price (₹)", min_value=0.0, value=50.0, step=5.0)
        pack_cost = st.number_input("Packaging Cost (₹)", min_value=0.0, value=10.0, step=1.0)
        ship_fee = st.number_input("Estimated Shipping / Platform Fee (₹)", min_value=0.0, value=55.0, step=5.0)
        profit = st.number_input("Target Net Profit (₹)", min_value=0.0, value=50.0, step=5.0)
        gst_slab = st.selectbox("GST Rate (%)", [3, 5, 12, 18], index=0)
        net_wt = st.number_input("Product Net Weight (g)", min_value=1, value=50)

    with c2:
        calc_selling_price = round(buy_cost + pack_cost + ship_fee + profit)
        suggested_mrp = max(calc_selling_price * 2, 299)
        taxable_val = round(calc_selling_price / (1 + (gst_slab / 100)), 2)
        gst_included = round(calc_selling_price - taxable_val, 2)
        st.markdown(f"""<div class="b-card"><div class="c-title">LISTING SUMMARY</div><div class="c-val">₹{calc_selling_price}</div><p><b>Suggested MRP:</b> ₹{suggested_mrp} | <b>Taxable Value:</b> ₹{taxable_val} | <b>GST ({gst_slab}%):</b> ₹{gst_included}</p></div>""", unsafe_allow_html=True)
        if st.button("💾 Save Product to Catalog Sheet"):
            new_cat = pd.DataFrame([{"SKU": sku, "Product_Name": prod_name, "Buy_Cost": buy_cost, "Packaging_Cost": pack_cost, "Platform_Fee": ship_fee, "Profit_Margin": profit, "Selling_Price": calc_selling_price, "Suggested_MRP": suggested_mrp, "GST_Rate": gst_slab, "Net_Weight_g": net_wt}])
            conn.update(worksheet="Catalog", data=pd.concat([cat_df, new_cat], ignore_index=True))
            st.success("Saved to Catalog!")
            st.rerun()
    st.dataframe(cat_df, use_container_width=True)

# ==========================================
# 5. SALES & INVOICES
# ==========================================
elif nav == "🧾 Sales & Invoices":
    st.subheader("Add New Sale / Order (GST Auto-Split)")
    with st.form("sales_form"):
        sc1, sc2, sc3 = st.columns(3)
        s_date = sc1.date_input("Order Date", date.today())
        s_inv = sc2.text_input("Invoice / Order ID", f"GK-{len(sales_df)+101}")
        s_plat = sc3.selectbox("Platform", ["Meesho", "Amazon", "Flipkart", "Direct"])
        sc4, sc5, sc6, sc7 = st.columns(4)
        s_prod = sc4.text_input("Product Name", "Gold-Plated Necklace Set")
        s_sku = sc5.text_input("SKU", "GK-NK-001")
        s_qty = sc6.number_input("Quantity", min_value=1, value=1)
        s_price = sc7.number_input("Total Selling Price (₹)", min_value=1.0, value=199.0)
        s_gst = st.selectbox("Applicable GST %", [3, 5, 12, 18], index=0)
        if st.form_submit_button("✅ Save Order to Google Sheets"):
            total_val = s_qty * s_price
            taxable = round(total_val / (1 + (s_gst / 100)), 2)
            total_tax = round(total_val - taxable, 2)
            cgst = round(total_tax / 2, 2)
            sgst = round(total_tax - cgst, 2)
            new_sale = pd.DataFrame([{"Date": str(s_date), "Invoice_No": s_inv, "Platform": s_plat, "Product_Name": s_prod, "SKU": s_sku, "Qty": s_qty, "Selling_Price": s_price, "GST_Rate": s_gst, "Taxable_Value": taxable, "CGST": cgst, "SGST": sgst, "Total": total_val}])
            conn.update(worksheet="Sales", data=pd.concat([sales_df, new_sale], ignore_index=True))
            st.success(f"Order {s_inv} saved!")
            st.rerun()

# ==========================================
# 6. PURCHASES & ITC
# ==========================================
elif nav == "📦 Purchases (ITC)":
    st.subheader("Log Wholesale Purchase Bills (Track Input Tax Credit)")
    with st.form("purchase_form"):
        pc1, pc2, pc3 = st.columns(3)
        p_date = pc1.date_input("Bill Date", date.today())
        p_bill = pc2.text_input("Wholesale Bill No.")
        p_supp = pc3.text_input("Wholesaler Name")
        pc4, pc5, pc6 = st.columns(3)
        p_cat = pc4.selectbox("Category", ["Imitation Jewellery", "Hair Accessories", "Packaging Material", "Other"])
        p_total = pc5.number_input("Total Bill Paid (₹)", min_value=1.0, value=2000.0)
        p_gst = pc6.selectbox("GST % on Bill", [3, 5, 12, 18], index=0)
        if st.form_submit_button("📥 Save Wholesale Bill & Claim ITC"):
            p_taxable = round(p_total / (1 + (p_gst / 100)), 2)
            p_itc = round(p_total - p_taxable, 2)
            new_purch = pd.DataFrame([{"Date": str(p_date), "Bill_No": p_bill, "Supplier_Name": p_supp, "Category": p_cat, "Total_Bill_Amount": p_total, "GST_Rate": p_gst, "Taxable_Amount": p_taxable, "ITC_Claimed": p_itc}])
            conn.update(worksheet="Purchases", data=pd.concat([purch_df, new_purch], ignore_index=True))
            st.success(f"Bill saved! ₹{p_itc} ITC added.")
            st.rerun()
