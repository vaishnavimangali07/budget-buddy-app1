import streamlit as st
import sqlite3
import matplotlib.pyplot as plt
import datetime
import hashlib
import pandas as pd

# ======================================================
# DB SETUP
# ======================================================
conn = sqlite3.connect("budget.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    username TEXT,
    type TEXT,
    account TEXT,
    category TEXT,
    amount REAL,
    date TEXT
)
""")

conn.commit()

# ======================================================
# PASSWORD HASH
# ======================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Budget Buddy", layout="centered")
st.write("App updated 🚀")

# ======================================================
# UI STYLE
# ======================================================
st.markdown("""
<style>
body {background-color: #eef2ff;}
.block-container {max-width: 420px; margin: auto;}
#MainMenu, footer, header {visibility: hidden;}
.header {
    background: linear-gradient(135deg, #6d28d9, #2563eb);
    padding: 20px; border-radius: 20px; color: white;
    text-align: center; margin-bottom: 15px;
}
.card {
    background: white; padding: 15px; border-radius: 18px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    margin-bottom: 15px;
}
.stButton button {
    background: linear-gradient(135deg, #2563eb, #4f46e5);
    color: white; border-radius: 12px; width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# SESSION STATE
# ======================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if "accounts" not in st.session_state:
    st.session_state.accounts = ["Cash", "Wallet"]

if "account_balances" not in st.session_state:
    st.session_state.account_balances = {}

if "show_account_form" not in st.session_state:
    st.session_state.show_account_form = False

# ======================================================
# BANK LIST
# ======================================================
BANK_LIST = [
    "SBI","HDFC","ICICI","Axis Bank",
    "Kotak Bank","Canara Bank",
    "Union Bank","Bank of Baroda",
    "Punjab National Bank",
    "IndusInd Bank",
    "Paytm Wallet","PhonePe Wallet","Google Pay (GPay)"
]

# ======================================================
# LOGIN / SIGNUP
# ======================================================
if not st.session_state.logged_in:

    st.title("💰 Budget Buddy")
    option = st.radio("Select Option", ["Login", "Create Account"])

    if option == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.button("Login"):
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hash_password(p)))
            result = c.fetchone()

            if result:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:
        u = st.text_input("New Username")
        p = st.text_input("New Password", type="password")

        if st.button("Sign Up"):
            if u == "" or p == "":
                st.warning("Fill all fields")
            else:
                try:
                    c.execute("INSERT INTO users VALUES (?, ?)", (u, hash_password(p)))
                    conn.commit()
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                except:
                    st.warning("User already exists")

    st.stop()

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.title(st.session_state.user)

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

page = st.sidebar.selectbox("Navigate", ["Dashboard", "Add Transaction"])

# ======================================================
# LOAD DATA
# ======================================================
c.execute("SELECT rowid, type, account, category, amount, date FROM transactions WHERE username=?", (st.session_state.user,))
rows = c.fetchall()

data = []
for r in rows:
    data.append({
        "id": r[0],
        "type": r[1],
        "account": r[2],
        "category": r[3],
        "amount": r[4],
        "date": r[5]
    })

# ======================================================
# DASHBOARD
# ======================================================
if page == "Dashboard":

    st.markdown(f"""
    <div class="header">
        <h2>💰 Budget Buddy</h2>
        <p>Welcome, {st.session_state.user}</p>
    </div>
    """, unsafe_allow_html=True)

    # ==============================
    # FILTER UI (NEW)
    # ==============================
    if data:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🔍 Filters")

        categories = ["All"] + list(set(d["category"] for d in data))
        selected_category = st.selectbox("Category", categories)

        start_date = st.date_input("Start Date", datetime.date.today())
        end_date = st.date_input("End Date", datetime.date.today())

        st.markdown('</div>', unsafe_allow_html=True)

        # APPLY FILTER
        filtered_data = []
        for d in data:
            d_date = datetime.datetime.strptime(d["date"], "%Y-%m-%d").date()

            if selected_category != "All" and d["category"] != selected_category:
                continue

            if not (start_date <= d_date <= end_date):
                continue

            filtered_data.append(d)
    else:
        filtered_data = []

    if data:

        income = sum(d["amount"] for d in filtered_data if d["type"]=="Income")
        expense = sum(d["amount"] for d in filtered_data if d["type"]=="Expense")

        accounts = st.session_state.account_balances.copy()

        for d in filtered_data:
            acc = d.get("account","Cash")

            if acc not in accounts:
                accounts[acc] = 0

            if d["type"]=="Income":
                accounts[acc] += d["amount"]
            else:
                accounts[acc] -= d["amount"]

        balance = sum(accounts.values())

        # Metrics
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        c1.metric("Income", income)
        c2.metric("Expense", expense)
        c3.metric("Balance", balance)
        st.markdown('</div>', unsafe_allow_html=True)

        # History + Delete (FILTERED)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📄 Transactions History")

        for d in filtered_data:
            col1, col2 = st.columns([4,1])

            with col1:
                st.write(f"{d['date']} | {d['type']} | {d['category']} | ₹{d['amount']}")

            with col2:
                if st.button("❌", key=d["id"]):
                    c.execute("DELETE FROM transactions WHERE rowid=?", (d["id"],))
                    conn.commit()
                    st.success("Deleted!")
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # Download
        df = pd.DataFrame(filtered_data)
        st.download_button("📥 Download Report", df.to_csv(index=False), "budget_report.csv")

    else:
        st.info("No data yet")

# ======================================================
# ADD TRANSACTION
# ======================================================
else:

    st.title("➕ Add Transaction")

    t = st.selectbox("Type",["Income","Expense"])
    acc = st.selectbox("Account", st.session_state.accounts)
    cat = st.selectbox("Category",["Food","Travel","Bills","Shopping","Salary","Other"])
    amt = st.number_input("Amount",min_value=0.0)
    date = st.date_input("Date",datetime.date.today())

    if st.button("Add"):
        if amt <= 0:
            st.warning("Enter valid amount")
        else:
            c.execute(
                "INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)",
                (st.session_state.user, t, acc, cat, amt, str(date))
            )
            conn.commit()
            st.success("Added 🎉")
            st.rerun()