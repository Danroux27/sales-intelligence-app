import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(layout="wide")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# -----------------------------
# SIMPLE USER SYSTEM (STABLE)
# -----------------------------
DEFAULT_USERS = {
    "admin": "1234",
    "test": "1234"
}

if "users" not in st.session_state:
    st.session_state.users = DEFAULT_USERS.copy()

# -----------------------------
# LOGIN / SIGNUP
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
                st.success("✅ Account created! Now log in.")

    elif mode == "Login":

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
st.title(f"📊 Sales Intelligence System - {user}")

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

USER_FILE = f"{DATA_FOLDER}/{user}.csv"

uploaded_file = st.file_uploader("Upload Daily Sales Sheet", type=["xlsx"])

if uploaded_file:

    df_new = pd.read_excel(uploaded_file)
    df_new.columns = df_new.columns.str.strip()

    st.success("File uploaded ✅")

    # Save history
    if os.path.exists(USER_FILE):
        df_history = pd.read_csv(USER_FILE)
        df_all = pd.concat([df_history, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(USER_FILE, index=False)

    # -----------------------------
    # PROCESS DATA
    # -----------------------------
    summary_data = []

    for person in df_new["Salesperson"].unique():

        person_df = df_new[df_new["Salesperson"] == person]

        calls = person_df["Calls"].sum()
        meetings = person_df["Meetings"].sum()
        quotes = person_df["Quotes Sent"].sum()
        deals_value = person_df["Deals Closed (R)"].sum()

        deal_count = len(person_df[person_df["Status"] == "Won"])
        pipeline = person_df[person_df["Status"].isin(["New", "Quoted"])]["Value (R)"].sum()

        call_to_quote = (quotes / calls * 100) if calls else 0
        quote_to_deal = (deal_count / quotes * 100) if quotes else 0

        revenue_per_call = (deals_value / calls) if calls else 0
        avg_deal_size = (deals_value / deal_count) if deal_count else 0

        # SCORING
        activity_score = min(calls / 30 * 100, 100)
        conversion_score = (call_to_quote + quote_to_deal) / 2
        revenue_score = min(deals_value / 50000 * 100, 100)

        score = (activity_score * 0.4 +
                 conversion_score * 0.4 +
                 revenue_score * 0.2)

        # -----------------------------
        # INSIGHTS
        # -----------------------------
        insights = []
        actions = []

        if calls > 20 and quote_to_deal < 20:
            insights.append("High activity but low closing rate")
            actions.append("Improve closing techniques")

        if calls < 10:
            insights.append("Low activity levels")
            actions.append("Increase outreach")

        if pipeline > 50000 and deal_count == 0:
            insights.append("Strong pipeline but no conversions")
            actions.append("Focus on follow-ups")

        if revenue_per_call > 2000:
            insights.append("High revenue efficiency")
            actions.append("Maintain performance")

        if deal_count > 3:
            insights.append("Strong closing ability")
            actions.append("Use as benchmark")

        summary_data.append({
            "name": person,
            "calls": calls,
            "meetings": meetings,
            "quotes": quotes,
            "deals_value": deals_value,
            "deal_count": deal_count,
            "pipeline": pipeline,
            "call_to_quote": call_to_quote,
            "quote_to_deal": quote_to_deal,
            "rev_per_call": revenue_per_call,
            "avg_deal": avg_deal_size,
            "score": score,
            "insights": insights,
            "actions": actions
        })

    df_summary = pd.DataFrame(summary_data)

    # -----------------------------
    # DASHBOARD
    # -----------------------------
    total_revenue = df_summary["deals_value"].sum()
    team_score = df_summary["score"].mean()
    top = df_summary.sort_values("score", ascending=False).iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Revenue", f"R{total_revenue:,.0f}")
    col2.metric("📊 Team Score", f"{team_score:.1f}/100")
    col3.metric("👑 Top Performer", top["name"])

    st.markdown("---")

    # -----------------------------
    # CHARTS
    # -----------------------------
    st.subheader("📊 Performance Score")
    st.bar_chart(df_summary.set_index("name")["score"])

    st.subheader("💰 Revenue by Salesperson")
    st.bar_chart(df_summary.set_index("name")["deals_value"])

    st.subheader("📞 Calls vs Deals")
    st.bar_chart(df_summary.set_index("name")[["calls", "deal_count"]])

    funnel_df = pd.DataFrame({
        "Stage": ["Calls", "Quotes", "Deals"],
        "Count": [
            df_summary["calls"].sum(),
            df_summary["quotes"].sum(),
            df_summary["deal_count"].sum()
        ]
    }).set_index("Stage")

    st.subheader("📉 Sales Funnel")
    st.bar_chart(funnel_df)

    st.markdown("---")

    # -----------------------------
    # SUMMARY
    # -----------------------------
    st.subheader("🧠 Manager Summary")
    st.write(f"""
    The team generated R{total_revenue:,.0f} in revenue with an average score of {team_score:.1f}/100.

    {top['name']} is the top performer today.
    """)

    # -----------------------------
    # INDIVIDUAL PERFORMANCE
    # -----------------------------
    st.subheader("👤 Individual Performance")

    for row in summary_data:

        st.markdown(f"### {row['name']} (Score: {row['score']:.1f}/100)")

        st.write(f"Calls: {row['calls']} | Meetings: {row['meetings']} | Quotes: {row['quotes']}")
        st.write(f"Deals: R{row['deals_value']:,.0f} ({row['deal_count']} deals)")
        st.write(f"Pipeline: R{row['pipeline']:,.0f}")

        st.write(f"Conversion: {row['call_to_quote']:.1f}% → {row['quote_to_deal']:.1f}%")
        st.write(f"Revenue/Call: R{row['rev_per_call']:.0f} | Avg Deal: R{row['avg_deal']:.0f}")

        st.markdown("**Insights:**")
        for i in row["insights"]:
            st.write(f"- {i}")

        st.markdown("**Recommended Actions:**")
        for a in row["actions"]:
            st.write(f"- {a}")

        st.markdown("---")

    # -----------------------------
    # DOWNLOAD REPORT
    # -----------------------------
    st.subheader("📄 Download Report")

    today = datetime.now().strftime("%Y-%m-%d")

    html = f"<h1>Sales Report</h1><p>Date: {today}</p>"
    html += f"<p>Total Revenue: R{total_revenue:,.0f}</p>"
    html += f"<p>Team Score: {team_score:.1f}</p>"

    st.download_button(
        label="⬇ Download Report",
        data=html,
        file_name=f"report_{today}.html",
        mime="text/html"
    )
