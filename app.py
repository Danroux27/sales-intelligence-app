import streamlit as st
import pandas as pd
import os
from datetime import datetime

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
    st.title(f"📊 Sales Intelligence System")
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

    # Layout split
    main_col, side_col = st.columns([3,1])

    summary_data = []

    for person in df["Salesperson"].unique():

        person_df = df[df["Salesperson"] == person]

        calls = person_df["Calls"].sum()
        quotes = person_df["Quotes Sent"].sum()
        deals_value = person_df["Deals Closed (R)"].sum()
        deal_count = len(person_df[person_df["Status"] == "Won"])

        call_to_quote = (quotes / calls * 100) if calls else 0
        quote_to_deal = (deal_count / quotes * 100) if quotes else 0

        score = (calls * 0.3) + (quote_to_deal * 0.5) + (deals_value / 1000 * 0.2)

        insights = []
        actions = []

        if calls > 20 and quote_to_deal < 20:
            insights.append("High activity but poor closing")
            actions.append("Work on closing")

        if calls < 10:
            insights.append("Low activity")
            actions.append("Increase calls")

        summary_data.append({
            "name": person,
            "calls": calls,
            "quotes": quotes,
            "deals": deals_value,
            "deal_count": deal_count,
            "c2q": call_to_quote,
            "q2d": quote_to_deal,
            "score": score,
            "insights": insights,
            "actions": actions
        })

    df_summary = pd.DataFrame(summary_data)

    total_revenue = df_summary["deals"].sum()
    team_score = df_summary["score"].mean()

    # -----------------------------
    # MAIN CONTENT (LEFT)
    # -----------------------------
    with main_col:

        col1, col2 = st.columns(2)
        col1.metric("Revenue", f"R{total_revenue:,.0f}")
        col2.metric("Team Score", f"{team_score:.1f}/100")

        st.markdown("## Manager Summary")
        st.write("Team performance overview with opportunities to improve conversions.")

        st.markdown("---")

        st.markdown("## Individual Performance")

        for row in summary_data:

            st.write(f"### {row['name']} (Score: {row['score']:.1f})")

            st.write(f"Calls: {row['calls']} | Quotes: {row['quotes']}")
            st.write(f"Deals: R{row['deals']:,.0f}")

            st.write(f"Conversion: {row['c2q']:.1f}% → {row['q2d']:.1f}%")

            st.write("Insights:")
            for i in row["insights"]:
                st.write(f"- {i}")

            st.write("Actions:")
            for a in row["actions"]:
                st.write(f"- {a}")

            st.markdown("---")

    # -----------------------------
    # SIDE CONTENT (RIGHT)
    # -----------------------------
    with side_col:

        st.markdown("### 📊 Quick Insights")

        st.bar_chart(df_summary.set_index("name")["score"])

        st.bar_chart(df_summary.set_index("name")["deals"])

        st.bar_chart(df_summary.set_index("name")[["calls", "deal_count"]])
