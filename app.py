import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Lead Rescue Pro",
    layout="wide"
)

# ==================================================
# SESSION STATE
# ==================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# ==================================================
# USER SYSTEM
# ==================================================
DEFAULT_USERS = {
    "admin": "1234",
    "manager": "1234",
    "test": "1234"
}

if "users" not in st.session_state:
    st.session_state.users = DEFAULT_USERS.copy()

# ==================================================
# LOGIN PAGE
# ==================================================
if not st.session_state.logged_in:

    st.markdown(
        "<h1 style='text-align:center;'>🚀 Lead Rescue Pro</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center;'>Modern Revenue Command Center</p>",
        unsafe_allow_html=True
    )

    mode = st.radio("Select Option", ["Login", "Sign Up"], horizontal=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    users = st.session_state.users

    if mode == "Sign Up":
        if st.button("Create Account", use_container_width=True):
            if username == "" or password == "":
                st.warning("Enter username and password.")
            elif username in users:
                st.error("User already exists.")
            else:
                users[username] = password
                st.session_state.users = users
                st.success("Account created. Please log in.")

    else:
        if st.button("Login", use_container_width=True):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid login.")

    st.stop()

# ==================================================
# MAIN APP
# ==================================================
user = st.session_state.user

top_left, top_right = st.columns([6, 1])

with top_left:
    st.markdown(
        "<h1 style='margin-bottom:0;'>📊 Lead Rescue Pro</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<p style='margin-top:0;'>Welcome back, <b>{user}</b> 👋</p>",
        unsafe_allow_html=True
    )

with top_right:
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("---")

uploaded_file = st.file_uploader(
    "Upload Sales Sheet",
    type=["xlsx"]
)

# ==================================================
# NO FILE STATE
# ==================================================
if not uploaded_file:
    st.info("Upload an Excel file to begin.")
    st.stop()

# ==================================================
# LOAD DATA
# ==================================================
df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.strip()

summary_data = []

# ==================================================
# PROCESS DATA
# ==================================================
for person in df["Salesperson"].unique():

    person_df = df[df["Salesperson"] == person]

    calls = person_df["Calls"].sum()
    meetings = person_df["Meetings"].sum() if "Meetings" in df.columns else 0
    quotes = person_df["Quotes Sent"].sum()
    deals_value = person_df["Deals Closed (R)"].sum()

    deal_count = len(person_df[person_df["Status"] == "Won"])

    pipeline = (
        person_df[
            person_df["Status"].isin(["New", "Quoted", "Negotiating"])
        ]["Value (R)"].sum()
        if "Value (R)" in df.columns else 0
    )

    call_to_quote = (quotes / calls * 100) if calls else 0
    quote_to_deal = (deal_count / quotes * 100) if quotes else 0

    revenue_per_call = (deals_value / calls) if calls else 0
    avg_deal_size = (deals_value / deal_count) if deal_count else 0

    # ------------------------------
    # SCORE MODEL
    # ------------------------------
    activity_score = min(calls / 30 * 100, 100)
    conversion_score = (call_to_quote + quote_to_deal) / 2
    revenue_score = min(deals_value / 50000 * 100, 100)

    score = (
        activity_score * 0.35 +
        conversion_score * 0.45 +
        revenue_score * 0.20
    )

    # ------------------------------
    # INSIGHTS / ACTIONS
    # ------------------------------
    actions = []
    insights = []

    if calls < 15:
        insights.append("Low activity.")
        actions.append("Increase outbound calls immediately.")

    if call_to_quote < 20:
        insights.append("Weak lead qualification.")
        actions.append("Improve pitch and qualification process.")

    if quote_to_deal < 20:
        insights.append("Poor closing velocity.")
        actions.append("Manager should review stalled quotes.")

    if pipeline > deals_value:
        insights.append("Strong pipeline not converting.")
        actions.append("Prioritise closing open opportunities.")

    if quote_to_deal > 40:
        insights.append("Strong closer.")
        actions.append("Use as benchmark for team coaching.")

    summary_data.append({
        "name": person,
        "calls": calls,
        "meetings": meetings,
        "quotes": quotes,
        "deals": deals_value,
        "deal_count": deal_count,
        "pipeline": pipeline,
        "c2q": call_to_quote,
        "q2d": quote_to_deal,
        "rev_per_call": revenue_per_call,
        "avg_deal": avg_deal_size,
        "score": score,
        "insights": insights,
        "actions": actions
    })

df_summary = pd.DataFrame(summary_data)

# ==================================================
# GLOBAL METRICS
# ==================================================
total_revenue = df_summary["deals"].sum()
pipeline_total = df_summary["pipeline"].sum()
team_score = df_summary["score"].mean()

top = df_summary.sort_values("score", ascending=False).iloc[0]
low = df_summary.sort_values("score").iloc[0]

revenue_at_risk = max(pipeline_total - total_revenue, 0)

# ==================================================
# AI RULE ENGINE
# ==================================================
alerts = []
recommendations = []

# Rule 1: High pipeline low close rate
for _, row in df_summary.iterrows():
    if row["pipeline"] >= 50000 and row["q2d"] < 20:
        alerts.append(
            f"🔴 {row['name']} has R{row['pipeline']:,.0f} pipeline at risk due to low close rate."
        )

# Rule 2: Low activity
for _, row in df_summary.iterrows():
    if row["calls"] < 10:
        alerts.append(
            f"🟠 {row['name']} activity is below target ({row['calls']} calls)."
        )

# Rule 3: Strong performer available
for _, row in df_summary.iterrows():
    if row["score"] > 75:
        recommendations.append(
            f"🟢 {row['name']} is performing strongly. Consider routing premium leads here."
        )

# Rule 4: Overall risk
if team_score < 55:
    alerts.append("🔴 Team score below target. Immediate management intervention advised.")

# General recommendations
if pipeline_total > total_revenue:
    recommendations.append(
        "🚀 Pipeline exceeds closed revenue. Focus team on closing existing opportunities."
    )

if df_summary["q2d"].mean() < 20:
    recommendations.append(
        "📞 Closing rate is weak. Run a focused follow-up and objection-handling session."
    )

# ==================================================
# KPI BAR
# ==================================================
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("💰 Revenue Won", f"R{total_revenue:,.0f}")
k2.metric("📈 Pipeline", f"R{pipeline_total:,.0f}")
k3.metric("🎯 Team Score", f"{team_score:.1f}/100")
k4.metric("⚠️ Revenue At Risk", f"R{revenue_at_risk:,.0f}")
k5.metric("👑 Top Performer", top["name"])

st.markdown("---")

# ==================================================
# COMMAND CENTER TOP SECTION
# ==================================================
left_main, right_main = st.columns([2, 1])

with left_main:

    st.markdown("## 🧠 Revenue Command Briefing")

    st.write(
        f"""
The team generated **R{total_revenue:,.0f}** in closed revenue with an overall score of **{team_score:.1f}/100**.

**{top['name']}** is leading performance, while **{low['name']}** requires immediate attention.

Current pipeline sits at **R{pipeline_total:,.0f}**, creating a strong opportunity if conversion improves.
"""
    )

    st.markdown("### 🚨 Priority Feed")

    if alerts:
        for item in alerts:
            st.warning(item)
    else:
        st.success("No urgent issues detected.")

    st.markdown("### 🚀 AI Recommendations")

    if recommendations:
        for item in recommendations:
            st.success(item)
    else:
        st.info("No recommendations at this time.")

with right_main:

    st.markdown("## 🏆 Team Rankings")

    rank_df = df_summary[["name", "score", "deals"]].sort_values(
        "score", ascending=False
    )
    st.dataframe(
        rank_df,
        use_container_width=True,
        hide_index=True
    )

# ==================================================
# LOWER SECTION
# ==================================================
st.markdown("---")

left_col, right_col = st.columns([2, 1])

# ==================================================
# INDIVIDUAL PERFORMANCE
# ==================================================
with left_col:

    st.markdown("## 👤 Individual Performance")

    for _, row in df_summary.sort_values("score", ascending=False).iterrows():

        st.markdown(
            f"### {row['name']} — Score {row['score']:.1f}/100"
        )

        st.write(
            f"Calls: {row['calls']} | Meetings: {row['meetings']} | Quotes: {row['quotes']}"
        )
        st.write(
            f"Deals Closed: {row['deal_count']} (R{row['deals']:,.0f})"
        )
        st.write(
            f"Pipeline: R{row['pipeline']:,.0f}"
        )
        st.write(
            f"Conversion: {row['c2q']:.1f}% → {row['q2d']:.1f}%"
        )
        st.write(
            f"Revenue / Call: R{row['rev_per_call']:,.0f} | Avg Deal: R{row['avg_deal']:,.0f}"
        )

        st.write("**Recommended Actions:**")

        if row["actions"]:
            for act in row["actions"]:
                st.write(f"- {act}")
        else:
            st.write("- Maintain current momentum.")

        st.markdown("---")

# ==================================================
# GRAPH PANEL
# ==================================================
with right_col:

    st.markdown("### 📊 Performance Score")
    st.bar_chart(df_summary.set_index("name")["score"])

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("### 📊 Revenue Generated")
    st.bar_chart(df_summary.set_index("name")["deals"])

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("### 📊 Pipeline vs Closed")
    st.bar_chart(
        df_summary.set_index("name")[["pipeline", "deals"]]
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown("### 📊 Quote to Deal %")
    st.bar_chart(df_summary.set_index("name")["q2d"])
