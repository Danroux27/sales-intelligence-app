import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(layout="wide")

# -----------------------------
# SIMPLE USER SYSTEM
# -----------------------------
USERS = {
    "admin": "1234",
    "test": "1234"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# -----------------------------
# LOGIN PAGE
# -----------------------------
if not st.session_state.logged_in:

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username] == password:
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

# -----------------------------
# UPLOAD FILE
# -----------------------------
uploaded_file = st.file_uploader("Upload Daily Sales Sheet", type=["xlsx"])

if uploaded_file:

    df_new = pd.read_excel(uploaded_file)
    df_new.columns = df_new.columns.str.strip()

    st.success("File uploaded ✅")

    # SAVE USER DATA
    if os.path.exists(USER_FILE):
        df_history = pd.read_csv(USER_FILE)
        df_all = pd.concat([df_history, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(USER_FILE, index=False)

    # -----------------------------
    # PROCESS DATA (FULL LOGIC)
    # -----------------------------
    summary_data = []

    for person in df_new["Salesperson"].unique():

        person_df = df_new[df_new["Salesperson"] == person]

        calls = person_df["Calls"].sum()
        meetings = person_df["Meetings"].sum()
        quotes = person_df["Quotes Sent"].sum()
        deals_value = person_df["Deals Closed (R)"].sum()

        deal_count = len(person_df[person_df["Status"] == "Won"])
        pipeline = person_df[person_df["Status"].isin(["New","Quoted"])]["Value (R)"].sum()

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
            "score": score
        })

    df_summary = pd.DataFrame(summary_data)

    # -----------------------------
    # DASHBOARD
    # -----------------------------
    total_revenue = df_summary["deals_value"].sum()
    team_score = df_summary["score"].mean()

    top = df_summary.sort_values("score", ascending=False).iloc[0]
    low = df_summary.sort_values("score").iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Revenue", f"R{total_revenue:,.0f}")
    col2.metric("📊 Team Score", f"{team_score:.1f}/100")
    col3.metric("👑 Top Performer", top["name"])

    if team_score > 75:
        st.success("🔥 High Performance Team")
    elif team_score > 50:
        st.warning("⚖️ Stable Performance")
    else:
        st.error("⚠️ Performance Needs Attention")

    st.markdown("---")

    # -----------------------------
    # SUMMARY
    # -----------------------------
    st.markdown("## 🧠 Manager Summary")

    st.write(f"""
    The team generated R{total_revenue:,.0f} in revenue with an overall performance score of {team_score:.1f}/100.

    {top['name']} led performance, while {low['name']} requires attention.

    Focus should be placed on improving conversion and closing outstanding opportunities.
    """)

    # -----------------------------
    # INDIVIDUAL PERFORMANCE
    # -----------------------------
    st.markdown("## 👤 Individual Performance")

    for row in summary_data:

        st.write(f"### {row['name']} (Score: {row['score']:.1f}/100)")
        st.write(f"Calls: {row['calls']} | Meetings: {row['meetings']} | Quotes: {row['quotes']}")
        st.write(f"Deals Closed: {row['deal_count']} (R{row['deals_value']:,.0f})")
        st.write(f"Pipeline: R{row['pipeline']:,.0f}")
        st.write(f"Conversion: {row['call_to_quote']:.1f}% → {row['quote_to_deal']:.1f}%")
        st.write(f"Revenue/Call: R{row['rev_per_call']:.0f} | Avg Deal: R{row['avg_deal']:.0f}")

        st.markdown("---")

    # -----------------------------
    # HTML REPORT DOWNLOAD
    # -----------------------------
    st.markdown("## 📄 Download Report")

    today = datetime.now().strftime("%Y-%m-%d")

    html = f"""
    <html>
    <body style="font-family: Arial; padding:20px;">
    <h1>Sales Report</h1>
    <p>Date: {today}</p>

    <h2>Summary</h2>
    <p>Revenue: R{total_revenue:,.0f}</p>
    <p>Team Score: {team_score:.1f}/100</p>
    <p>Top Performer: {top['name']}</p>

    <h2>Team Performance</h2>
    <table border="1" cellspacing="0" cellpadding="5">
    <tr>
    <th>Name</th><th>Calls</th><th>Quotes</th><th>Deals</th><th>Score</th>
    </tr>
    """

    for row in summary_data:
        html += f"""
        <tr>
        <td>{row['name']}</td>
        <td>{row['calls']}</td>
        <td>{row['quotes']}</td>
        <td>R{row['deals_value']:,.0f}</td>
        <td>{row['score']:.1f}</td>
        </tr>
        """

    html += "</table></body></html>"

    st.download_button(
        label="⬇ Download Report",
        data=html,
        file_name=f"sales_report_{today}.html",
        mime="text/html"
    )
