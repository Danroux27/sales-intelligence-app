import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# -----------------------------
# USER SYSTEM
# -----------------------------
DEFAULT_USERS = {
    "admin": "1234",
    "test": "1234"
}

if "users" not in st.session_state:
    st.session_state.users = DEFAULT_USERS.copy()

# -----------------------------
# LOGIN PAGE
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

top1, top2 = st.columns([6,1])

with top1:
    st.title("📊 Sales Intelligence System")
    st.markdown(f"<h4 style='text-align:center;'>Welcome, {user} 👋</h4>", unsafe_allow_html=True)

with top2:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("---")

uploaded_file = st.file_uploader("Upload Daily Sales Sheet", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    summary_data = []

    for person in df["Salesperson"].unique():

        person_df = df[df["Salesperson"] == person]

        calls = person_df["Calls"].sum()
        meetings = person_df["Meetings"].sum() if "Meetings" in df.columns else 0
        quotes = person_df["Quotes Sent"].sum()
        deals_value = person_df["Deals Closed (R)"].sum()

        deal_count = len(person_df[person_df["Status"] == "Won"])

        pipeline = person_df[
            person_df["Status"].isin(["New", "Quoted"])
        ]["Value (R)"].sum() if "Value (R)" in df.columns else 0

        call_to_quote = (quotes / calls * 100) if calls else 0
        quote_to_deal = (deal_count / quotes * 100) if quotes else 0

        revenue_per_call = (deals_value / calls) if calls else 0
        avg_deal_size = (deals_value / deal_count) if deal_count else 0

        activity_score = min(calls / 30 * 100, 100)
        conversion_score = (call_to_quote + quote_to_deal) / 2
        revenue_score = min(deals_value / 50000 * 100, 100)

        score = (
            activity_score * 0.4 +
            conversion_score * 0.4 +
            revenue_score * 0.2
        )

        insights = []
        actions = []

        if calls < 15:
            insights.append("Low activity levels")
            actions.append("Increase outbound calls")

        if call_to_quote < 20:
            insights.append("Weak call-to-quote conversion")
            actions.append("Improve pitch and qualification")

        if quote_to_deal < 20:
            insights.append("Low closing rate")
            actions.append("Focus on follow-ups and closing techniques")

        if pipeline > deals_value:
            insights.append("Pipeline is strong but not converting")
            actions.append("Prioritise closing existing deals")

        if quote_to_deal > 40:
            insights.append("Strong closer")
            actions.append("Maintain performance")

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

    total_revenue = df_summary["deals"].sum()
    team_score = df_summary["score"].mean()

    # -----------------------------
    # TOP METRICS
    # -----------------------------
    col1, col2 = st.columns(2)
    col1.metric("Total Revenue", f"R{total_revenue:,.0f}")
    col2.metric("Team Score", f"{team_score:.1f}/100")

    st.markdown("---")

    # -----------------------------
    # TOP SECTION (CLEAN)
    # -----------------------------
    top = df_summary.sort_values("score", ascending=False).iloc[0]
    low = df_summary.sort_values("score").iloc[0]

    st.markdown("## 🧠 Manager Summary")

    st.write(f"""
    The team generated R{total_revenue:,.0f} in revenue with an overall performance score of {team_score:.1f}/100.

    **{top['name']}** is currently leading performance, while **{low['name']}** requires attention.

    The biggest opportunity lies in improving conversion rates and closing pipeline opportunities.
    """)

    st.markdown("---")

    st.markdown("## 🏆 Team Rankings")
    st.write(f"Top Performer: **{top['name']}** ({top['score']:.1f}/100)")
    st.write(f"Needs Attention: **{low['name']}** ({low['score']:.1f}/100)")

    st.markdown("---")

    st.markdown("## ⚠️ Key Issues")

    if team_score < 50:
        st.error("Overall team performance is low — urgent improvement required")

    if df_summary["q2d"].mean() < 20:
        st.warning("Low closing rate — deals are not converting")

    if df_summary["calls"].mean() < 15:
        st.warning("Low activity levels across the team")

    st.markdown("---")

    st.markdown("## 🚀 Opportunities")

    if df_summary["pipeline"].sum() > total_revenue:
        st.success("Strong pipeline — focus on closing existing deals")

    if team_score > 60:
        st.success("Team efficiency is improving")

    st.markdown("---")

    # -----------------------------
    # TEAM ACTION PLAN
    # -----------------------------
    st.markdown("## 🧭 Team Action Plan")

    st.write("""
    - Increase daily call targets for low-activity salespeople  
    - Implement structured follow-ups on all outstanding quotes  
    - Focus on closing deals already in the pipeline before chasing new leads  
    - Top performers should share techniques with the team  
    - Review pricing, objections, and closing scripts weekly  
    """)

    st.markdown("---")

    # -----------------------------
    # BOTTOM SECTION
    # -----------------------------
    left_col, right_col = st.columns([2,1])

    # LEFT: INDIVIDUAL PERFORMANCE
    with left_col:
        st.markdown("## 👤 Individual Performance")

        for row in summary_data:

            st.write(f"### {row['name']} (Score: {row['score']:.1f})")

            st.write(f"Calls: {row['calls']} | Meetings: {row['meetings']} | Quotes: {row['quotes']}")
            st.write(f"Deals: R{row['deals']:,.0f} ({row['deal_count']} deals)")
            st.write(f"Pipeline: R{row['pipeline']:,.0f}")

            st.write(f"Conversion: {row['c2q']:.1f}% → {row['q2d']:.1f}%")

            st.write(f"Revenue/Call: R{row['rev_per_call']:.0f}")
            st.write(f"Avg Deal Size: R{row['avg_deal']:.0f}")

            st.write("**Recommended Actions:**")

            if row["calls"] < 15:
                st.write("- Increase outbound calls — activity is too low")

            if row["c2q"] < 20:
                st.write("- Improve pitch — leads are not converting to quotes")

            if row["q2d"] < 20:
                st.write("- Focus on closing — follow up more aggressively")

            if row["pipeline"] > row["deals"]:
                st.write("- Prioritise closing pipeline deals before chasing new leads")

            if row["q2d"] > 40:
                st.write("- Strong closer — maintain performance and mentor others")

            st.markdown("---")

    # RIGHT: GRAPHS
    with right_col:
        st.markdown("### 📊 Performance Score")
        st.bar_chart(df_summary.set_index("name")["score"])

        st.markdown("<br><br><br>", unsafe_allow_html=True)

        st.markdown("### 📊 Revenue Generated")
        st.bar_chart(df_summary.set_index("name")["deals"])

        st.markdown("<br><br><br>", unsafe_allow_html=True)

        st.markdown("### 📊 Pipeline vs Revenue")
        st.bar_chart(df_summary.set_index("name")[["pipeline", "deals"]])
