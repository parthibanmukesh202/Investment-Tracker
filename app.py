import streamlit as st
import pandas as pd
from datetime import date
import matplotlib.pyplot as plt
import numpy as np
from streamlit_gsheets import GSheetsConnection

# --- APP CONFIG ---
st.set_page_config(page_title="Investment Dashboard", layout="wide")

# Google Sheets Connection setup
conn = st.connection("gsheets", type=GSheetsConnection)

# --- CUSTOM STYLING ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stMetricValue"] { color: #2e7d32; font-size: 1.8rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #555; font-size: 1rem; }
    .stButton>button { 
        background-color: #2e7d32; 
        color: white; border-radius: 8px; border: none; height: 3em; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: #1b5e20; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: LOGIN & ACCESS ---
st.sidebar.title("🔐 User Access")
user_name = st.sidebar.text_input("Username", value="").strip()
password = st.sidebar.text_input("Password", type="password")

# --- XIRR MATH FUNCTION ---
def calculate_xirr(cashflows, dates, guess=0.1):
    if len(cashflows) < 2: return 0.0
    if all(x >= 0 for x in cashflows) or all(x <= 0 for x in cashflows): return 0.0
    years = [(pd.to_datetime(d) - pd.to_datetime(dates[0])).days / 365.25 for d in dates]
    rate = guess
    for _ in range(100):
        try:
            rate = max(min(rate, 10.0), -0.99) 
            f = sum([cf / (1 + rate)**t for cf, t in zip(cashflows, years)])
            df = sum([-t * cf / (1 + rate)**(t + 1) for cf, t in zip(cashflows, years)])
            if df == 0: break
            new_rate = rate - f / df
            if abs(new_rate - rate) < 1e-6: return new_rate
            rate = new_rate
        except: return 0.0
    return 0.0

# --- MAIN DASHBOARD LOGIC ---
if user_name and password == "invest123":
    
    # 1. LOAD DATA FROM CLOUD
    try:
        all_data = conn.read(ttl=0)
    except:
        all_data = pd.DataFrame(columns=["User", "Date", "Cashflow"])

    # 2. FILTER FOR USER (Syntax Fixed Here)
    user_data = all_data[all_data["User"] == user_name].copy()
    
    if user_data.empty:
        user_data = pd.DataFrame({"User": [user_name], "Date": [str(date(2023, 1, 1))], "Cashflow": [-3000.0]})

    st.title("💰 Investment Dashboard")
    st.markdown(f'<p style="font-size:1.2rem;">Welcome, <b>{user_name}</b>! | Dashboard by Mukesh Parthiban</p>', unsafe_allow_html=True)
    st.divider()

    # --- UI LAYOUT ---
    col_left, col_right = st.columns([1.2, 1], gap="large")

    with col_left:
        st.subheader("🗓️ Cashflow Journal")
        
        # Display Table
        edited_df = st.data_editor(
            user_data[["Date", "Cashflow"]],
            num_rows="dynamic",
            use_container_width=True,
            height=400,
            column_config={
                "Cashflow": st.column_config.NumberColumn("Amount (₹)", format="₹ %.2f"),
                "Date": st.column_config.DateColumn("Date")
            }
        )

        if st.button("💾 SAVE DATA PERMANENTLY"):
            other_users = all_data[all_data["User"] != user_name] if not all_data.empty else pd.DataFrame()
            edited_df["User"] = user_name
            final_df = pd.concat([other_users, edited_df], ignore_index=True)
            conn.update(data=final_df)
            st.success("Changes saved to Cloud!")
            st.rerun()

    with col_right:
        st.subheader("📌 Investment Summary")
        df_calc = edited_df.dropna().copy()
        df_calc['Date'] = pd.to_datetime(df_calc['Date'])
        df_calc = df_calc.sort_values("Date")
        
        if not df_calc.empty:
            total_invested = abs(df_calc[df_calc["Cashflow"] < 0]["Cashflow"].sum())
            net_value = df_calc["Cashflow"].sum() + total_invested 
            total_return_amt = net_value - total_invested
            abs_return_pct = (total_return_amt / total_invested) if total_invested > 0 else 0
            
            xirr_val = calculate_xirr(df_calc["Cashflow"].tolist(), df_calc["Date"].tolist())

            m1, m2 = st.columns(2)
            m1.metric("💸 Total Invested", f"₹ {total_invested:,.0f}")
            m2.metric("💰 Net Value", f"₹ {net_value:,.0f}")
            st.divider()
            m3, m4 = st.columns(2)
            m3.metric("📈 Total Return", f"₹ {total_return_amt:,.0f}")
            m4.metric("🎯 XIRR", f"{xirr_val:.2%}")
            
            st.markdown(f"**Absolute Return:** {abs_return_pct:.2%}")

            if total_invested > 0:
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.pie([total_invested, max(0, total_return_amt)], 
                       labels=["Investment", "Profit"], autopct='%1.1f%%', 
                       colors=['#cfd8dc', '#4caf50'], startangle=140)
                center_circle = plt.Circle((0,0), 0.70, fc='white')
                fig.gca().add_artist(center_circle)
                st.pyplot(fig)

    # --- LOWER SECTION (SIP CALCULATOR) ---
    st.divider()
    st.subheader("🚀 Future Value Projections")
    calc_type = st.radio("Calculator Mode:", ["🔄 SIP Mode", "🏦 Lumpsum Mode"], horizontal=True)

    in1, in2, in3 = st.columns(3)
    if "SIP" in calc_type:
        inv_amt = in1.number_input("Monthly SIP (₹)", value=10000)
        expected_return = in2.number_input("Expected Return (%)", value=12.0)
        tenure_years = in3.number_input("Years", value=15)
        m_rate = expected_return / 12 / 100
        total_m = int(tenure_years * 12)
        total_inv = inv_amt * total_m
        final_corpus = inv_amt * (((1 + m_rate)**total_m - 1) / m_rate) * (1 + m_rate)
        chart_pts = [inv_amt * (((1 + m_rate)**m - 1) / m_rate) * (1 + m_rate) for m in range(1, total_m + 1)]
    else:
        inv_amt = in1.number_input("Lumpsum Investment (₹)", value=100000)
        expected_return = in2.number_input("Expected Return (%)", value=12.0)
        tenure_years = in3.number_input("Years", value=15)
        total_inv = inv_amt
        final_corpus = inv_amt * (1 + expected_return/100)**tenure_years
        chart_pts = [inv_amt * (1 + expected_return/100)**y for y in range(1, int(tenure_years) + 1)]

    out1, out2, out3 = st.columns(3)
    out1.metric("💰 Total Invested", f"₹ {total_inv:,.0f}")
    out2.metric("📈 Returns Earned", f"₹ {final_corpus - total_inv:,.0f}")
    out3.metric("🏦 Future Corpus", f"₹ {final_corpus:,.0f}")
    st.line_chart(chart_pts, color="#2e7d32")

elif user_name and password != "invest123":
    st.sidebar.error("Incorrect Password!")
else:
    st.title("🔒 Investment Dashboard")
    st.info("Please enter your Username and Password on the sidebar to access your private dashboard.")
    st.write("Default Password for testing: **invest123**")
