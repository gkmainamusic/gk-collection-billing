import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# Page Setup
st.set_page_config(page_title="GK Collection — Billoora Suite", page_icon="💎", layout="wide")

st.title("💎 GK Collection — E-Commerce & GST Billing Suite")
st.caption("Guwahati, Assam | Fashion Jewellery & Accessories Management")

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

# Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard & GST Summary", 
    "🏷️ Meesho/Amazon Price Calculator", 
    "🧾 Sales & GST Entry", 
    "📦 Wholesale & ITC Tracker"
])

# --- TAB 1: DASHBOARD & GST SUMMARY ---
with tab1:
    st.subheader("Business Overview & GST Ledger")
    
    total_sales = pd.to_numeric(sales_df["Total"], errors='coerce').sum() if not sales_df.empty else 0.0
    total_purchases = pd.to_numeric(purch_df["Total_Bill_Amount"], errors='coerce').sum() if not purch_df.empty else 0.0
    
    output_gst = (pd.to_numeric(sales_df["CGST"], errors='coerce').sum() + pd.to_numeric(sales_df["SGST"], errors='coerce').sum()) if not sales_df.empty else 0.0
    input_itc = pd.to_numeric(purch_df["ITC_Claimed"], errors='coerce').sum() if not purch_df.empty else 0.0
    net_gst_payable = max(0.0, output_gst - input_itc)
    itc_credit_balance = max(0.0, input_itc - output_gst)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sales (Revenue)", f"₹{total_sales:,.2f}")
    col2.metric("Total Wholesale Purchases", f"₹{total_purchases:,.2f}")
    col3.metric("Output GST (Collected)", f"₹{output_gst:,.2f}", f"ITC Available: ₹{input_itc:,.2f}")
    col4.metric("Net GST Payable", f"₹{net_gst_payable:,.2f}", f"Credit Balance: ₹{itc_credit_balance:,.2f}")

    st.divider()
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("**Recent Orders / Sales**")
        st.dataframe(sales_df.tail(10), use_container_width=True)
    with col_right:
        st.write("**Recent Wholesale Bills (ITC)**")
        st.dataframe(purch_df.tail(10), use_container_width=True)

# --- TAB 2: PRICE & CATALOG CALCULATOR ---
with tab2:
    st.subheader("Meesho / Amazon Listing Price & MRP Calculator")
    c1, c2 = st.columns(2)
    
    with c1:
        sku = st.text_input("SKU Code (e.g., GK-NK-001)", "GK-BR-001")
        prod_name = st.text_input("Product Title", "GK Collection Gold-Plated Bracelet")
        buy_cost = st.number_input("Wholesale Buy Price (₹)", min_value=0.0, value=50.0, step=5.0)
        pack_cost = st.number_input("Packaging Cost (Box + Sticker + Card) (₹)", min_value=0.0, value=10.0, step=1.0)
        ship_fee = st.number_input("Estimated Shipping / Platform Deduction (₹)", min_value=0.0, value=55.0, step=5.0)
        profit = st.number_input("Your Target Net Profit (₹)", min_value=0.0, value=50.0, step=5.0)
        gst_slab = st.selectbox("GST Rate on Purchase Bill (%)", [3, 5, 12, 18], index=0)
        net_wt = st.number_input("Product Net Weight (grams)", min_value=1, value=50)

    with c2:
        calc_selling_price = round(buy_cost + pack_cost + ship_fee + profit)
        suggested_mrp = max(calc_selling_price * 2, 299)
        taxable_val = round(calc_selling_price / (1 + (gst_slab / 100)), 2)
        gst_included = round(calc_selling_price - taxable_val, 2)
        discount_pct = round(((suggested_mrp - calc_selling_price) / suggested_mrp) * 100)

        st.info("### 📌 Listing Summary (Copy to Meesho/Amazon)")
        st.write(f"**Final Listing (Selling) Price:** `₹{calc_selling_price}` *(GST Inclusive)*")
        st.write(f"**Suggested MRP:** `₹{suggested_mrp}` *(Shows {discount_pct}% OFF)*")
        st.write(f"**Inside Price Breakdown:** Basic Value: `₹{taxable_val}` | Included GST ({gst_slab}%): `₹{gst_included}`")
        st.write(f"**Packet Shipping Weight (Approx):** `{net_wt + 40}g` (with box & flyer)")

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

    st.divider()
    st.write("**Saved Catalog Products**")
    st.dataframe(cat_df, use_container_width=True)

# --- TAB 3: SALES & GST INVOICE ---
with tab3:
    st.subheader("Add New Sale / Order (GST Auto-Split)")
    with st.form("sales_form"):
        sc1, sc2, sc3 = st.columns(3)
        s_date = sc1.date_input("Order Date", date.today())
        s_inv = sc2.text_input("Invoice / Order ID", f"GK-{len(sales_df)+101}")
        s_plat = sc3.selectbox("Platform", ["Meesho", "Amazon", "Flipkart", "Direct/Instagram"])
        
        sc4, sc5, sc6, sc7 = st.columns(4)
        s_prod = sc4.text_input("Product Name", "Gold-Plated Necklace Set")
        s_sku = sc5.text_input("SKU", "GK-NK-001")
        s_qty = sc6.number_input("Quantity", min_value=1, value=1)
        s_price = sc7.number_input("Total Selling Price (GST Inclusive ₹)", min_value=1.0, value=199.0)
        
        s_gst = st.selectbox("Applicable GST % (As per Bill)", [3, 5, 12, 18], index=0)
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
            st.success(f"Order {s_inv} saved! Taxable: ₹{taxable} | CGST: ₹{cgst} | SGST: ₹{sgst}")
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
        p_gst = pc6.selectbox("GST % Mentioned at Bottom of Bill", [3, 5, 12, 18], index=0)

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
            st.success(f"Wholesale Bill saved! Input Tax Credit (ITC) of ₹{p_itc} added to your ledger.")
            st.rerun()