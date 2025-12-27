# ================= RIGHT =================
with right:
    st.subheader("📊 Investment Summary")

    df = df_user.dropna()
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")

        # 1. Total Amount you actually put into the system
        total_invested = abs(df[df["Cashflow"] < 0]["Cashflow"].sum())
        
        # 2. Total Amount you have taken out
        total_withdrawn = df[df["Cashflow"] > 0]["Cashflow"].sum()
        
        # 3. Current Net Value (remaining principle + gains)
        # Formula: (Sum of all cashflows) * -1 if you want to see current "Skin in the game"
        # However, for a simple absolute profit view:
        net_cashflow = df["Cashflow"].sum()
        
        # 4. Absolute Profit
        # If net_cashflow is positive, you've withdrawn more than invested.
        # If negative, that's your remaining capital/value.
        profit = total_withdrawn - total_invested 

        # --- Metrics Display ---
        m1, m2 = st.columns(2)
        m1.metric("💸 Total Invested", f"₹ {total_invested:,.0f}")
        m2.metric("📤 Total Withdrawn", f"₹ {total_withdrawn:,.0f}")

        m3, m4, m5 = st.columns(3)
        # Using delta to show if you are in green or red
        m3.metric("📈 Net Gain/Loss", f"₹ {profit:,.0f}", delta=f"{profit:,.0f}")
        
        # CAGR and XIRR logic remains the same
        years = (df["Date"].max() - df["Date"].min()).days / 365
        cagr = (total_withdrawn / total_invested) ** (1 / years) - 1 if total_invested > 0 and years > 0 and total_withdrawn > 0 else 0
        xirr = calculate_xirr(df["Cashflow"].tolist(), df["Date"].tolist())

        m4.metric("📊 CAGR", f"{cagr*100:.2f}%")
        m5.metric("🎯 XIRR", f"{xirr*100:.2f}%")
