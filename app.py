import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# -----------------------------
# SIMPLE USER SYSTEM
# -----------------------------
DEFAULT_USERS = {
    "admin": "1234",
    "test": "1234"
}

if "users" not in st.session_state:
    st.session_state.users = DEFAULT_USERS.copy()

# -----------------------------
# LOGIN
# -----------------------------
if not st.session_state.logged_in:

    st.title("🚀 Sales Intelligence System")

    mode = st.radio("Select Option", ["Login", "Sign Up"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    users = st.session_state.users

    if mode == "Sign Up":
        if st.button("Create Account"):
            if username == "" or password == "":
                st.warning("Enter username and password")
            elif username in users:
                st.error("User already exists")
            else:
                users[username] = password
                st.session_state.users = users
                st.success("Account created")

    else:
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid login")

    st.stop()

# -----------------------------
# MAIN APP
# -----------------------------
user = st.session_state.user

col_top1, col_top2 = st.columns([6,1])

with col_top1:
    st.title("📊 Sales Intelligence System")
    st.write(f"Welcome, **{user}**")

with col_top2:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("---")

uploaded_file = st.file_uploader("Upload Daily Sales Sheet", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    main_col, side_col = st.columns([3,1])

    summary_data = []

    for person in df["Salesperson"].unique():

        person_df = df[df["Salesperson"] == person]

        calls = person_df["Calls"].sum()
        quotes = person_df["Quotes Sent"].sum()
        deals_value = person_df["Deals Closed (R)"].sum()
        deal_count = len(person_df[person_df["Status"] == "Won"])

        pipeline = person_df[person_df["Status"].isin(["New","Quoted"])]["Value (R)"].sum()

        call_to_quote = (quotes / calls * 100) if calls else 0
        quote_to_deal = (deal_count / quotes * 100) if quotes else 0

        revenue_per_call = (deals_value / calls) if calls else 0
        avg_deal = (deals_value / deal_count) if deal_count else 0

        score = (calls * 0.3) + (quote_to_deal * 0.5) + (deals_value / 1000 * 0.2)

        summary_data.append({
            "name": person,
            "calls": calls,
            "quotes": quotes,
            "deals": deals_value,
            "deal_count": deal_count,
            "pipeline": pipeline,
            "c2q": call_to_quote,
            "q2d": quote_to_deal,
            "rpc": revenue_per_call,
            "avg_deal": avg_deal,
            "score": score
        })

    df_summary = pd.DataFrame(summary_data)

    total_revenue = df_summary["deals"].sum()
    team_score = df_summary["score"].mean()

    avg_close = df_summary["q2d"].mean()
    avg_rpc = df_summary["rpc"].mean()

    # -----------------------------
    # MAIN CONTENT
    # -----------------------------
    with main_col:

        col1, col2 = st.columns(2)
        col1.metric("Revenue", f"R{total_revenue:,.0f}")
        col2.metric("Team Score", f"{team_score:.1f}/100")

        st.markdown("## Manager Summary")

        st.write(f"""
        The team generated R{total_revenue:,.0f} in revenue.

        Average closing rate is {avg_close:.1f}% and revenue efficiency sits at R{avg_rpc:,.0f} per call.

        Key opportunity: improving conversion after quote stage.
        """)

        st.markdown("---")

        st.markdown("## Individual Performance")

        for _, row in df_summary.iterrows():

            st.write(f"### {row['name']} (Score: {row['score']:.1f})")

            st.write(f"Calls: {row['calls']} | Quotes: {row['quotes']}")
            st.write(f"Deals: R{row['deals']:,.0f} ({row['deal_count']} deals)")
            st.write(f"Pipeline: R{row['pipeline']:,.0f}")

            st.write(f"Conversion: {row['c2q']:.1f}% → {row['q2d']:.1f}%")
            st.write(f"Revenue/Call: R{row['rpc']:.0f} | Avg Deal: R{row['avg_deal']:.0f}")

            # SMART INSIGHTS
            if row["q2d"] < avg_close:
                st.write("⚠ Closing below team average")

            if row["rpc"] > avg_rpc:
                st.write("🔥 Strong revenue efficiency")

            if row["pipeline"] > row["deals"]:
                st.write("📈 Strong pipeline — focus on conversion")

            st.markdown("---")

    # -----------------------------
    # SIDE CONTENT (IMPROVED CHARTS)
    # -----------------------------
    with side_col:

        st.markdown("### 📊 Funnel")

        funnel_df = pd.DataFrame({
            "Stage": ["Calls", "Quotes", "Deals"],
            "Value": [
                df_summary["calls"].sum(),
                df_summary["quotes"].sum(),
                df_summary["deal_count"].sum()
            ]
        }).set_index("Stage")

        st.bar_chart(funnel_df)

        st.markdown("### 🎯 Revenue per Call")
        st.bar_chart(df_summary.set_index("name")["rpc"])

        st.markdown("### 📍 Performance Map")

        fig, ax = plt.subplots()
        ax.scatter(df_summary["calls"], df_summary["deals"])

        for i, txt in enumerate(df_summary["name"]):
            ax.annotate(txt, (df_summary["calls"][i], df_summary["deals"][i]))

        ax.set_xlabel("Calls")
        ax.set_ylabel("Revenue")

        st.pyplot(fig)
