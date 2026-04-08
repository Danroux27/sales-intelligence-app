import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

st.set_page_config(layout="wide")

# -----------------------------
# STYLE (UI IMPROVEMENT)
# -----------------------------
st.markdown("""
<style>
.main {
    text-align: center;
}
.block-container {
    padding-top: 2rem;
    max-width: 900px;
    margin: auto;
}
h1, h2, h3 {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# USER DATABASE
# -----------------------------
USER_FILE = "users.json"

if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

with open(USER_FILE, "r") as f:
    USERS = json.load(f)

# -----------------------------
# SESSION
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# -----------------------------
# LOGIN / SIGNUP PAGE
# -----------------------------
if not st.session_state.logged_in:

    st.title("🚀 Sales Intelligence System")

    menu = st.radio("Select Option", ["Login", "Sign Up"], horizontal=True)

    if menu == "Login":

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid login")

    else:
        new_user = st.text_input("Create Username")
        new_pass = st.text_input("Create Password", type="password")

        if st.button("Sign Up"):
            if new_user in USERS:
                st.error("User already exists")
            else:
                USERS[new_user] = new_pass
                with open(USER_FILE, "w") as f:
                    json.dump(USERS, f)

                st.success("Account created! You can now login")

    st.stop()

# -----------------------------
# MAIN APP
# -----------------------------
user = st.session_state.user

st.title("📊 Sales Intelligence Dashboard")
st.markdown(f"### Welcome, **{user}** 👋")

# Logout
if st.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

USER_DATA = f"{DATA_FOLDER}/{user}.csv"

# -----------------------------
# UPLOAD
# -----------------------------
st.markdown("### 📂 Upload Daily Sales Sheet")
uploaded_file = st.file_uploader("", type=["xlsx"])

if uploaded_file:

    df_new = pd.read_excel(uploaded_file)
    df_new.columns = df_new.columns.str.strip()

    st.success("File uploaded successfully ✅")

    # SAVE DATA
    if os.path.exists(USER_DATA):
        df_history = pd.read_csv(USER_DATA)
        df_all = pd.concat([df_history, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(USER_DATA, index=False)

    # -----------------------------
    # PROCESS DATA
    # -----------------------------
    summary_data = []

    for person in df_new["Salesperson"].unique():

        person_df = df_new[df_new["Salesperson"] == person]

        calls = person_df["Calls"].sum()
        quotes = person_df["Quotes Sent"].sum()
        deals_value = person_df["Deals Closed (R)"].sum()
        deal_count = len(person_df[person_df["Status"] == "Won"])

        call_to_quote = (quotes / calls * 100) if calls else 0
        quote_to_deal = (deal_count / quotes * 100) if quotes else 0

        score = (call_to_quote + quote_to_deal) / 2

        summary_data.append({
            "name": person,
            "calls": calls,
            "quotes": quotes,
            "deals_value": deals_value,
            "score": score
        })

    df_summary = pd.DataFrame(summary_data)

    total_revenue = df_summary["deals_value"].sum()
    team_score = df_summary["score"].mean()

    top = df_summary.sort_values("score", ascending=False).iloc[0]

    st.markdown("---")

    # -----------------------------
    # DASHBOARD METRICS
    # -----------------------------
    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Revenue", f"R{total_revenue:,.0f}")
    col2.metric("📊 Team Score", f"{team_score:.1f}/100")
    col3.metric("👑 Top Performer", top["name"])

    st.markdown("---")

    # -----------------------------
    # INDIVIDUAL PERFORMANCE
    # -----------------------------
    st.markdown("## 👤 Team Performance")

    for row in summary_data:

        st.markdown(f"""
        ### {row['name']}  
        Calls: {row['calls']} | Quotes: {row['quotes']}  
        Deals: R{row['deals_value']:,.0f}  
        Score: {row['score']:.1f}/100  
        """)
