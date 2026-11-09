import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="GK Collection — Billoora Suite", page_icon="💎", layout="wide")

# Custom CSS to match Screenshot 1 UI
st.markdown("""
<style>
.stApp { background-color: #f4f6fb; color: #1e293b; }
.top-banner {
    background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
    padding: 18px 28px;
    border-radius: 14px;
    color: white;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
}
.brand-box { display: flex; align-items: center; gap: 14px; }
.logo-icon {
    background: #ea580c;
    color: white;
    font-weight: 800;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 20px;
    letter-spacing: 1px;
}
.pro-badge {
    background: rgba(234, 179, 8, 0.2);
    color: #facc15;
    border: 1px solid #eab308;
    font-size: 11px;
    padding: 2px 9px;
    border-radius: 12px;
    margin-left: 8px;
    font-weight: 700;
}
.b-card {
    background: #ffffff;
    padding: 22px;
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    margin-bottom: 16px;
}
.b-card-dark {
    background: #0f172a;
    padding: 22px;
    border-radius: 16px;
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(15,23,42,0.18);
    margin-bottom: 16px;
}
.c-title { font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.6px; }
.c-title-gold { font-size: 12px; font-weight: 700; color: #facc15; text-transform: uppercase; letter-spacing: 0.6px; }
.c-val { font-size: 30px; font-weight: 800; color: #0f172a; margin: 8px 0 4px 0; }
.c-val-white { font-size: 30px; font-weight: 800; color: #ffffff; margin: 8px 0 4px 0; }
.c-sub { font-size: 13px; color: #64748b; }
.c-sub-green { font-size: 13px; color: #16a34a; font-weight: 600; }
.c-sub-light { font-size: 13px; color: #94a3b8; }
.plat-row { margin-bottom: 16px; }
.plat-label { display: flex; justify-content: space-between; font-size: 14px; font-weight: 700; margin-bottom: 6px; }
.bar-bg { width: 100%; background: #f1f5f9; height: 10px; border-radius: 8px; overflow: hidden; }
</style>
<div class="top-banner">
<div class="brand-box">
<div class="logo-icon">GK</div>
<div>
<div style="font-size: 20px; font-weight: 700;">GK Collection <span class="pro-badge">PRO</span></div>
<div style="font-size: 12px; color: #94a3b8;">Billoora E-Com & GST Suite • Guwahati, Assam</div>
</div>
</div>
<div style="font-size: 13px; color: #cbd5e1;">Connected to Google Sheets Live DB</div>
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

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard & GST Summary", 
    "🏷️ Price Check & Calculator", 
    "🧾 + New Sale Entry", 
    "📦 Wholesale & ITC Tracker"
])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.markdown("### Business Overview & GST Dashboard")
    st.caption("Aapki Meesho, Amazon aur Wholesale kharidari ka live lekhajokha")

    total_sales = pd.to_numeric(sales_df["Total"], errors='coerce').sum() if not sales_df.empty else 0.0
    total_purchases = pd.to_numeric(purch_df["Total_Bill_Amount"], errors='coerce').sum() if not purch_df.empty else 0.0
    net_cash = total_sales - total_purchases

    output_gst = (pd.to_numeric(sales_df["CGST"], errors='coerce').sum() + pd.to_numeric(sales_df["SGST"], errors='coerce').sum()) if not sales_df.empty else 0.0
    input_itc = pd.to_numeric(purch_df["ITC_Claimed"], errors='coerce').sum() if not purch_df.empty else 0.0
    itc_balance = input_itc - output_gst

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown(f"""<div class="b-card">
<div class="c-title">TOTAL SALES (BIKRI) 📈</div>
<div class="c-val">₹{total_sales:,.0f}</div>
<div><span class="c-sub-green">GST Inclusive</span> <span class="c-sub">(Meesho/Amazon)</span></div>
</div>""", unsafe_allow_html=True)
    with r1c2:
        st.markdown(f"""<div class="b-card">
<div class="c-title">WHOLESALE & PACKING KHARCHA 🛒</div>
<div class="c-val">₹{total_purchases:,.0f}</div>
<div class="c-sub">Stock + Zip-lock, Labels & Cards</div>
</div>""", unsafe_allow_html=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown(f"""<div class="b-card">
<div class="c-title">NET CASH BALANCE / PROFIT 👛</div>
<div class="c-val">₹{net_cash:,.0f}</div>
<div class="c-sub">Sales minus Total Purchases</div>
</div>""", unsafe_allow_html=True)
    with r2c2:
        if itc_balance >= 0:
            gst_label = f"₹{itc_balance:,.2f} ITC"
            gst_sub = "Aapke paas Input Tax Credit jama hai"
        else:
            gst_label = f"₹{abs(itc_balance):,.2f} Payable"
            gst_sub = "Output GST minus ITC (Tax Dena Hai)"
        st.markdown(f"""<div class="b-card-dark">
<div class="c-title-gold">GST & ITC HISAB 🛡️</div>
<div class="c-val-white">{gst_label}</div>
<div class="c-sub-light">{gst_sub}</div>
</div>""", unsafe_allow_html=True)

    # Platform Breakdown Bar Card (Zero Indentation so Markdown renders HTML properly)
    def get_plat_sum(plat_name):
        if sales_df.empty:
            return 0.0
        sub = sales_df[sales_df["Platform"].astype(str).str.contains(plat_name, case=False, na=False)]
        return pd.to_numeric(sub["Total"], errors='coerce').sum()

    m_sales = get_plat_sum("Meesho")
    a_sales = get_plat_sum("Amazon")
    f_sales = get_plat_sum("Flipkart") + get_plat_sum("Direct")

    m_pct = round((m_sales / total_sales) * 100) if total_sales > 0 else 0
    a_pct = round((a_sales / total_sales) * 100) if total_sales > 0 else 0
    f_pct = round((f_sales / total_sales) * 100) if total_sales > 0 else 0

    st.markdown(f"""<div class="b-card">
<div style="font-size:16px; font-weight:700; color:#0f172a;">Platform-Wise Bikri (Meesho vs Amazon vs Flipkart)</div>
<div class="c-sub" style="margin-bottom:18px;">Kis marketplace se kitna revenue aa raha hai</div>
<div class="plat-row">
<div class="plat-label"><span style="color:#be185d;">Meesho Supplier Store</span><span>₹{m_sales:,.0f} ({m_pct}%)</span></div>
<div class="bar-bg"><div style="width:{m_pct}%; background:#db2777; height:100%;"></div></div>
</div>
<div class="plat-row">
<div class="plat-label"><span style="color:#b45309;">Amazon Seller Central</span><span>₹{a_sales:,.0f} ({a_pct}%)</span></div>
<div class="bar-bg"><div style="width:{a_pct}%; background:#f59e0b; height:100%;"></div></div>
</div>
<div class="plat-row">
<div class="plat-label"><span style="color:#1d4ed8;">Flipkart / Direct Orders</span><span>₹{f_sales:,.0f} ({f_pct}%)</span></div>
<div class="bar-bg"><div style="width:{f_pct}%; background:#2563eb; height:100%;"></div></div>
</div>
</div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.write("**Recent Orders / Sales**")
        st.dataframe(sales_df.tail(8), use_container_width=True)
    with col_r:
        st.write("**Recent Wholesale Bills (ITC)**")
        st.dataframe(purch_df.tail(8), use_container_width=True)

# --- TAB 2: PRICE CALCULATOR ---
with tab2:
    st.subheader("Meesho / Amazon Listing Price & MRP Calculator")
    c1, c2 = st.columns(2)
    with c1:
        sku = st.text_input("SKU Code", "GK-BR-001")
        prod_name = st.text_input("Product Title", "GK Collection Gold-Plated Bracelet")
        buy_cost = st.number_input("Wholesale Buy Price (₹)", min_value=0.0, value=50.0, step=5.0)
        pack_cost = st.number_input("Packaging Cost (Box + Pouch) (₹)", min_value=0.0, value=10.0, step=1.0)
        ship_fee = st.number_input("Estimated Shipping / Platform Fee (₹)", min_value=0.0, value=55.0, step=5.0)
        profit = st.number_input("Your Target Net Profit (₹)", min_value=0.0, value=50.0, step=5.0)
        gst_slab = st.selectbox("GST Rate on Purchase Bill (%)", [3, 5, 12, 18], index=0)
        net_wt = st.number_input("Product Net Weight (grams)", min_value=1, value=50)

    with c2:
        calc_selling_price = round(buy_cost + pack_cost + ship_fee + profit)
        suggested_mrp = max(calc_selling_price * 2, 299)
        taxable_val = round(calc_selling_price / (1 + (gst_slab / 100)), 2)
        gst_included = round(calc_selling_price - taxable_val, 2)
        discount_pct = round(((suggested_mrp - calc_selling_price) / suggested_mrp) * 100)

        st.markdown(f"""<div class="b-card">
<div class="c-title">📌 LISTING SUMMARY (COPY TO MEESHO/AMAZON)</div>
<div class="c-val">₹{calc_selling_price} <span style="font-size:14px; font-weight:500; color:#16a34a;">(GST Inclusive Selling Price)</span></div>
<p style="margin:8px 0;"><b>Suggested Catalog MRP:</b> ₹{suggested_mrp} <i>({discount_pct}% OFF)</i></p>
<p style="margin:8px 0;"><b>Tax Breakdown:</b> Taxable Value: ₹{taxable_val} | GST ({gst_slab}%): ₹{gst_included}</p>
<p style="margin:8px 0;"><b>Packed Courier Weight:</b> ~{net_wt + 40}g (with box & flyer)</p>
</div>""", unsafe_allow_html=True)

        if st.button("💾 Save Product to Catalog Sheet"):
            new_cat = pd.DataFrame([{
                "SKU": sku, "Product_Name": prod_name, "Buy_Cost": buy_cost,
                "Packaging_Cost": pack_cost, "Platform_Fee": ship_fee, "Profit_Margin": profit,
                "Selling_Price": calc_selling_price, "Suggested_MRP": suggested_mrp,
                "GST_Rate": gst_slab, "Net_Weight_g": net_wt
            }])
            updated_cat = pd.concat([cat_df, new_cat], ignore_index=True)
            conn.update(worksheet="Catalog", data=updated_cat)
            st.success("Product Catalog Google Sheet mein save ho gaya!")
            st.rerun()

    st.dataframe(cat_df, use_container_width=True)

# --- TAB 3: SALES ENTRY ---
with tab3:
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
        s_price = sc7.number_input("Total Selling Price (GST Inclusive ₹)", min_value=1.0, value=199.0)
        
        s_gst = st.selectbox("Applicable GST %", [3, 5, 12, 18], index=0)
        submit_sale = st.form_submit_button("✅ Save Order to Google Sheets")

        if submit_sale:
            total_val = s_qty * s_price
            taxable = round(total_val / (1 + (s_gst / 100)), 2)
            total_tax = round(total_val - taxable, 2)
            cgst = round(total_tax / 2, 2)
            sgst = round(total_tax - cgst, 2)

            new_sale = pd.DataFrame([{
                "Date": str(s_date), "Invoice_No": s_inv, "Platform": s_plat,
                "Product_Name": s_prod, "SKU": s_sku, "Qty": s_qty,
                "Selling_Price": s_price, "GST_Rate": s_gst,
                "Taxable_Value": taxable, "CGST": cgst, "SGST": sgst, "Total": total_val
            }])
            updated_sales = pd.concat([sales_df, new_sale], ignore_index=True)
            conn.update(worksheet="Sales", data=updated_sales)
            st.success(f"Order {s_inv} saved to Google Sheets!")
            st.rerun()

# --- TAB 4: WHOLESALE & ITC TRACKER ---
with tab4:
    st.subheader("Log Wholesale Purchase Bills (Track Input Tax Credit)")
    with st.form("purchase_form"):
        pc1, pc2, pc3 = st.columns(3)
        p_date = pc1.date_input("Bill Date", date.today())
        p_bill = pc2.text_input("Wholesale Bill / Invoice No.")
        p_supp = pc3.text_input("Wholesaler / Shop Name")

        pc4, pc5, pc6 = st.columns(3)
        p_cat = pc4.selectbox("Item Category", ["Imitation Jewellery", "Hair Accessories", "Packaging Material", "Other"])
        p_total = pc5.number_input("Total Bill Amount Paid (Inclusive of GST ₹)", min_value=1.0, value=2000.0)
        p_gst = pc6.selectbox("GST % Mentioned on Bill", [3, 5, 12, 18], index=0)

        submit_purch = st.form_submit_button("📥 Save Wholesale Bill & Claim ITC")

        if submit_purch:
            p_taxable = round(p_total / (1 + (p_gst / 100)), 2)
            p_itc = round(p_total - p_taxable, 2)

            new_purch = pd.DataFrame([{
                "Date": str(p_date), "Bill_No": p_bill, "Supplier_Name": p_supp,
                "Category": p_cat, "Total_Bill_Amount": p_total,
                "GST_Rate": p_gst, "Taxable_Amount": p_taxable, "ITC_Claimed": p_itc
            }])
            updated_purch = pd.concat([purch_df, new_purch], ignore_index=True)
            conn.update(worksheet="Purchases", data=updated_purch)
            st.success(f"Wholesale Bill saved! ₹{p_itc} ITC added.")
            st.rerun()
