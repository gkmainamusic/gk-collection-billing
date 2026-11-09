import streamlit as st
import pandas as pd
import json
import io
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="GK Collection — Billoora Suite", page_icon="💎", layout="wide")

# Custom CSS matching Billoora Suite UI
st.markdown("""
<style>
.stApp { background-color: #f8fafc; color: #0f172a; }
.top-banner {
    background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
    padding: 18px 26px;
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
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    margin-bottom: 16px;
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
</style>
<div class="top-banner">
<div class="brand-box">
<div class="logo-icon">GK</div>
<div>
<div style="font-size: 19px; font-weight: 700;">GK Collection — Billoora Suite</div>
<div style="font-size: 12px; color: #94a3b8;">Guwahati, Assam • GST & E-Commerce Automation</div>
</div>
</div>
<div style="font-size: 13px; color: #cbd5e1;">Connected to Google Sheets DB</div>
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
    if uploaded_file is None: return pd.DataFrame()
    try:
        return pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"File error: {e}")
        return pd.DataFrame()

def standardize_b2c_df(df, source_name, sign=1):
    if df.empty: return pd.DataFrame(columns=["Source", "POS", "GST_Rate", "Taxable_Value"])
    cols = {str(c).lower().strip(): c for c in df.columns}
    state_col = next((cols[k] for k in cols if any(w in k for w in ["end_customer_state", "customer_state", "ship to state", "destination state", "pos", "state"])), None)
    tax_col = next((cols[k] for k in cols if any(w in k for w in ["taxable", "net_taxable", "taxable_value", "principal"])), None)
    rate_col = next((cols[k] for k in cols if any(w in k for w in ["gst_rate", "tax_rate", "rate", "gst %"])), None)

    out = pd.DataFrame()
    out["Taxable_Value"] = pd.to_numeric(df[tax_col], errors="coerce").fillna(0.0) * sign if tax_col else 0.0
    out["GST_Rate"] = pd.to_numeric(df[rate_col], errors="coerce").fillna(3.0) if rate_col else 3.0
    out["POS"] = df[state_col].astype(str).str.upper().str.strip().apply(lambda val: next((s_code for s_name, s_code in STATE_MAP.items() if s_name in val or val.startswith(s_code)), "18")) if state_col else "18"
    out["Source"] = source_name
    return out[["Source", "POS", "GST_Rate", "Taxable_Value"]]

# Exact Billoora Sidebar Navigation (Matching Screenshots)
with st.sidebar:
    st.markdown("### 💎 BILLORA SUITE")
    user_gstin = st.text_input("GSTIN (Assam)", value="18AAAAA0000A1Z5")
    home_state_code = user_gstin[:2] if len(user_gstin) >= 2 else "18"
    st.divider()
    
    menu = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Khata Book",
            "Chat",
            "Connections",
            "Pricing",
            "Sales ➔ Invoices",
            "Purchases ➔ Bills",
            "Filings ➔ GSTR-1 Filing",
            "Filings ➔ GSTR-3B Filing",
            "Reports",
            "Parties",
            "Revenue",
            "Billing",
            "Settings"
        ]
    )

# 1. DASHBOARD
if menu == "Dashboard":
    st.subheader("Business Overview & GST Ledger")
    total_sales = pd.to_numeric(sales_df["Total"], errors='coerce').sum() if not sales_df.empty else 0.0
    total_purchases = pd.to_numeric(purch_df["Total_Bill_Amount"], errors='coerce').sum() if not purch_df.empty else 0.0
    net_cash = total_sales - total_purchases
    output_gst = (pd.to_numeric(sales_df["CGST"], errors='coerce').sum() + pd.to_numeric(sales_df["SGST"], errors='coerce').sum()) if not sales_df.empty else 0.0
    input_itc = pd.to_numeric(purch_df["ITC_Claimed"], errors='coerce').sum() if not purch_df.empty else 0.0
    itc_balance = input_itc - output_gst

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"""<div class="b-card"><div class="c-title">TOTAL SALES</div><div class="c-val">₹{total_sales:,.0f}</div><div class="c-sub">Meesho / Amazon / Flipkart</div></div>""", unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="b-card"><div class="c-title">TOTAL PURCHASES</div><div class="c-val">₹{total_purchases:,.0f}</div><div class="c-sub">Stock + Packaging</div></div>""", unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="b-card"><div class="c-title">NET CASH</div><div class="c-val">₹{net_cash:,.0f}</div><div class="c-sub">Sales minus Purchases</div></div>""", unsafe_allow_html=True)
    with c4: st.markdown(f"""<div class="b-card" style="background:#0f172a; color:#fff;"><div class="c-title" style="color:#facc15;">GST LEDGER</div><div class="c-val" style="color:#fff;">₹{itc_balance:,.2f}</div><div class="c-sub" style="color:#94a3b8;">Output GST: ₹{output_gst:,.2f}</div></div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**Recent Orders / Sales**")
        st.dataframe(sales_df.tail(8), use_container_width=True)
    with col_r:
        st.write("**Recent Bills (ITC)**")
        st.dataframe(purch_df.tail(8), use_container_width=True)

# 2. KHATA BOOK
elif menu == "Khata Book":
    st.subheader("📖 Khata Book — Credit Tracking Simplified")
    st.caption("Track credit given to customers and payments received, all in one place.")
    kc1, kc2, kc3 = st.columns(3)
    kc1.metric("Outstanding from Customers", "₹0")
    kc2.metric("Past Due Date", "₹0")
    kc3.metric("Net Balance", "₹0")
    st.divider()
    st.info("Khata Book customer records are active.")

# 3. CHAT
elif menu == "Chat":
    st.subheader("💬 Billoora AI Support Chat")
    st.text_input("Ask anything about GST filing or invoicing...")

# 4. CONNECTIONS
elif menu == "Connections":
    st.subheader("🔗 API & Platform Connections")
    st.checkbox("Meesho Supplier Panel API", value=True)
    st.checkbox("Amazon Seller Central API", value=True)
    st.checkbox("Flipkart Seller Hub API", value=True)

# 5. PRICING
elif menu == "Pricing":
    st.subheader("🏷️ Pricing & Catalog Calculator")
    c1, c2 = st.columns(2)
    with c1:
        sku = st.text_input("SKU Code", "GK-BR-001")
        prod_name = st.text_input("Product Title", "GK Collection Jewellery")
        buy_cost = st.number_input("Wholesale Buy Price (₹)", min_value=0.0, value=50.0, step=5.0)
        pack_cost = st.number_input("Packaging Cost (₹)", min_value=0.0, value=10.0, step=1.0)
        ship_fee = st.number_input("Platform Fee (₹)", min_value=0.0, value=55.0, step=5.0)
        profit = st.number_input("Target Net Profit (₹)", min_value=0.0, value=50.0, step=5.0)
        gst_slab = st.selectbox("GST Rate (%)", [3, 5, 12, 18], index=0)
    with c2:
        sp = round(buy_cost + pack_cost + ship_fee + profit)
        mrp = max(sp * 2, 299)
        st.markdown(f"""<div class="b-card"><div class="c-title">LISTING SUMMARY</div><div class="c-val">₹{sp}</div><p><b>Suggested MRP:</b> ₹{mrp}</p></div>""", unsafe_allow_html=True)
        if st.button("💾 Save Product to Catalog"):
            new_cat = pd.DataFrame([{"SKU": sku, "Product_Name": prod_name, "Buy_Cost": buy_cost, "Packaging_Cost": pack_cost, "Platform_Fee": ship_fee, "Profit_Margin": profit, "Selling_Price": sp, "Suggested_MRP": mrp, "GST_Rate": gst_slab, "Net_Weight_g": 50}])
            conn.update(worksheet="Catalog", data=pd.concat([cat_df, new_cat], ignore_index=True))
            st.success("Saved!")
            st.rerun()
    st.dataframe(cat_df, use_container_width=True)

# 6. SALES ➔ INVOICES
elif menu == "Sales ➔ Invoices":
    st.subheader("Invoice Dashboard — Sales & Billing")
    with st.form("sales_form"):
        sc1, sc2, sc3 = st.columns(3)
        s_date = sc1.date_input("Order Date", date.today())
        s_inv = sc2.text_input("Invoice ID", f"GK-{len(sales_df)+101}")
        s_plat = sc3.selectbox("Platform", ["Meesho", "Amazon", "Flipkart", "Direct"])
        sc4, sc5, sc6, sc7 = st.columns(4)
        s_prod = sc4.text_input("Product Name", "Necklace Set")
        s_sku = sc5.text_input("SKU", "GK-NK-001")
        s_qty = sc6.number_input("Quantity", min_value=1, value=1)
        s_price = sc7.number_input("Selling Price (₹)", min_value=1.0, value=199.0)
        s_gst = st.selectbox("GST %", [3, 5, 12, 18], index=0)
        if st.form_submit_button("✅ Issue / Save Invoice"):
            tot = s_qty * s_price
            taxable = round(tot / (1 + (s_gst / 100)), 2)
            tot_tax = round(tot - taxable, 2)
            cgst, sgst = round(tot_tax / 2, 2), round(tot_tax - (tot_tax / 2), 2)
            new_s = pd.DataFrame([{"Date": str(s_date), "Invoice_No": s_inv, "Platform": s_plat, "Product_Name": s_prod, "SKU": s_sku, "Qty": s_qty, "Selling_Price": s_price, "GST_Rate": s_gst, "Taxable_Value": taxable, "CGST": cgst, "SGST": sgst, "Total": tot}])
            conn.update(worksheet="Sales", data=pd.concat([sales_df, new_s], ignore_index=True))
            st.success("Invoice Saved!")
            st.rerun()
    st.dataframe(sales_df, use_container_width=True)

# 7. PURCHASES ➔ BILLS
elif menu == "Purchases ➔ Bills":
    st.subheader("Bills & Expenses — Track Vendor Bills")
    with st.form("p_form"):
        pc1, pc2, pc3 = st.columns(3)
        p_date = pc1.date_input("Date", date.today())
        p_bill = pc2.text_input("Bill No.")
        p_supp = pc3.text_input("Supplier Name")
        pc4, pc5, pc6 = st.columns(3)
        p_cat = pc4.selectbox("Category", ["Jewellery", "Packaging", "Other"])
        p_total = pc5.number_input("Total Amount Paid (₹)", min_value=1.0, value=2000.0)
        p_gst = pc6.selectbox("GST %", [3, 5, 12, 18], index=0)
        if st.form_submit_button("📥 Save Vendor Bill"):
            taxable = round(p_total / (1 + (p_gst / 100)), 2)
            itc = round(p_total - taxable, 2)
            new_p = pd.DataFrame([{"Date": str(p_date), "Bill_No": p_bill, "Supplier_Name": p_supp, "Category": p_cat, "Total_Bill_Amount": p_total, "GST_Rate": p_gst, "Taxable_Amount": taxable, "ITC_Claimed": itc}])
            conn.update(worksheet="Purchases", data=pd.concat([purch_df, new_p], ignore_index=True))
            st.success("Bill Saved!")
            st.rerun()
    st.dataframe(purch_df, use_container_width=True)

# 8. FILINGS ➔ GSTR-1 FILING
elif menu == "Filings ➔ GSTR-1 Filing":
    st.markdown("## 📄 GSTR-1 Filing")
    st.caption("Combine sales from Meesho, Flipkart, Amazon, and your invoices into a single GSTR-1 return[cite: 13].")

    p1, p2, p3 = st.columns(3)
    filing_type = p1.selectbox("Type of Filing *", ["Monthly", "Quarterly"])
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    sel_month = p2.selectbox("Month *", months_list, index=9)
    sel_year = p3.selectbox("Year *", ["2026", "2025", "2027"], index=0)
    fp_code = f"{str(months_list.index(sel_month) + 1).zfill(2)}{sel_year}"

    st.markdown("#### Platforms")
    col_m, col_f, col_a, col_b, col_man = st.columns(5)

    with col_m:
        st.markdown("""<div class="b-card"><span class="badge-b2c">B2C • MONTHLY</span><div style="font-weight:700; font-size:15px;">🛍️ Meesho</div><div class="c-sub" style="margin-bottom:8px;">Supplier Panel Reports</div></div>""", unsafe_allow_html=True)
        m_sales_file = st.file_uploader("Upload tcs_sales", type=["xlsx", "csv"], key="g1_m_sales")
        m_ret_file = st.file_uploader("Upload Return", type=["xlsx", "csv"], key="g1_m_ret")
    with col_f:
        st.markdown("""<div class="b-card"><span class="badge-b2c">B2C • MONTHLY</span><div style="font-weight:700; font-size:15px;">🛒 Flipkart</div><div class="c-sub" style="margin-bottom:8px;">Seller Hub Reports</div></div>""", unsafe_allow_html=True)
        f_sales_file = st.file_uploader("Upload Flipkart Sales", type=["xlsx", "csv"], key="g1_f_sales")
    with col_a:
        st.markdown("""<div class="b-card"><span class="badge-b2c">B2C • MONTHLY</span><div style="font-weight:700; font-size:15px;">📦 Amazon</div><div class="c-sub" style="margin-bottom:8px;">MTR B2C Report</div></div>""", unsafe_allow_html=True)
        a_sales_file = st.file_uploader("Upload Amazon MTR", type=["xlsx", "csv"], key="g1_a_sales")
    with col_b:
        st.markdown("""<div class="b-card"><span class="badge-b2c">Invoices • MONTHLY</span><div style="font-weight:700; font-size:15px;">🏢 Billoora DB</div><div class="c-sub" style="margin-bottom:8px;">Google Sheet DB Sales</div></div>""", unsafe_allow_html=True)
        inc_billoora = st.checkbox("Include Sheet Sales", value=True, key="g1_inc_db")
    with col_man:
        st.markdown("""<div class="b-card"><span class="badge-b2c">Upload • MONTHLY</span><div style="font-weight:700; font-size:15px;">📄 Manual</div><div class="c-sub" style="margin-bottom:8px;">Offline sales upload</div></div>""", unsafe_allow_html=True)
        man_file = st.file_uploader("Upload Manual Excel", type=["xlsx", "csv"], key="g1_man")

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🔍 Analyze & Generate GSTR-1 Return", type="primary", use_container_width=True)

    if analyze_btn or m_sales_file or f_sales_file or a_sales_file or man_file or inc_billoora:
        dfs = []
        if m_sales_file: dfs.append(standardize_b2c_df(read_uploaded_file(m_sales_file), "Meesho", 1))
        if m_ret_file: dfs.append(standardize_b2c_df(read_uploaded_file(m_ret_file), "Meesho Return", -1))
        if f_sales_file: dfs.append(standardize_b2c_df(read_uploaded_file(f_sales_file), "Flipkart", 1))
        if a_sales_file: dfs.append(standardize_b2c_df(read_uploaded_file(a_sales_file), "Amazon", 1))
        if man_file: dfs.append(standardize_b2c_df(read_uploaded_file(man_file), "Manual", 1))
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
                pos, rt, txval = str(row["POS"]).zfill(2), float(row["GST_Rate"]), round(float(row["Taxable_Value"]), 2)
                if txval == 0: continue
                is_intra = (pos == home_state_code)
                sply_ty = "INTRA" if is_intra else "INTER"
                if is_intra:
                    camt, samt, iamt = round(txval * (rt / 200.0), 2), round(txval * (rt / 200.0), 2), 0.0
                    entry = {"sply_ty": "INTRA", "pos": pos, "typ": "OE", "txval": txval, "rt": rt, "camt": camt, "samt": samt, "csamt": 0.0}
                else:
                    iamt, camt, samt = round(txval * (rt / 100.0), 2), 0.0, 0.0
                    entry = {"sply_ty": "INTER", "pos": pos, "typ": "OE", "txval": txval, "rt": rt, "iamt": iamt, "csamt": 0.0}
                b2cs_entries.append(entry)
                summary_rows.append({"POS": pos, "Supply Type": sply_ty, "Rate %": rt, "Taxable Value": txval, "IGST": iamt, "CGST": camt, "SGST": samt})

            sum_df = pd.DataFrame(summary_rows)
            st.divider()
            st.dataframe(sum_df, use_container_width=True)
            gstr1_json = {"gstin": user_gstin, "fp": fp_code, "version": "GST3.1.6", "b2cs": b2cs_entries}
            st.download_button("⬇️ Download JSON (for GST portal)[cite: 13]", json.dumps(gstr1_json, indent=2), f"GSTR1_{fp_code}.json", mime="application/json", type="primary", use_container_width=True)

# 9. FILINGS ➔ GSTR-3B FILING
elif menu == "Filings ➔ GSTR-3B Filing":
    st.markdown("## 📑 GSTR-3B Filing")
    st.caption("Outward supplies and ITC calculation for GSTR-3B return.")
    p1, p2, p3 = st.columns(3)
    p1.selectbox("Type of Filing *", ["Monthly", "Quarterly"])
    months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    p2.selectbox("Month *", months_list, index=9)
    p3.selectbox("Year *", ["2026", "2025", "2027"], index=0)
    st.file_uploader("Choose GSTR-2B .json file", type=["json"])
    
    tot_tx = pd.to_numeric(sales_df["Taxable_Value"], errors="coerce").sum() if not sales_df.empty else 0.0
    tot_cg = pd.to_numeric(sales_df["CGST"], errors="coerce").sum() if not sales_df.empty else 0.0
    tot_sg = pd.to_numeric(sales_df["SGST"], errors="coerce").sum() if not sales_df.empty else 0.0
    
    st.dataframe(pd.DataFrame([{"Taxable Value": tot_tx, "IGST": 0.0, "CGST": tot_cg, "SGST": tot_sg}]), use_container_width=True)
    gstr3b_json = {"gstin": user_gstin, "sup_details": {"osup_det": {"txval": tot_tx, "camt": tot_cg, "samt": tot_sg}}}
    st.download_button("⬇️ Download GSTR-3B JSON", json.dumps(gstr3b_json, indent=2), "GSTR3B.json", mime="application/json", type="primary", use_container_width=True)

# 10. OTHER MENUS
else:
    st.subheader(f"📁 {menu} Section")
    st.info(f"Aapka {menu} module active hai. Isme aap apne records manage kar sakte hain.")
