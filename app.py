import streamlit as st
import json
import matplotlib.pyplot as plt
import datetime
import hashlib

# ✅ TEST LINE (for deployment check)
st.write("App updated 🚀")

# ======================================================
# PASSWORD HASH FUNCTION
# ======================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Budget Buddy", layout="centered")

# ======================================================
# 🎨 UI
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
# AUTH
# ======================================================
USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

users = load_users()

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
            if u in users and users[u] == hash_password(p):
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Invalid credentials")

    else:
        u = st.text_input("New Username")
        p = st.text_input("New Password", type="password")

        if st.button("Sign Up"):
            if u in users:
                st.warning("User exists")
            elif u == "" or p == "":
                st.warning("Fill all fields")
            else:
                users[u] = hash_password(p)
                save_users(users)
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()

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
# DATA
# ======================================================
DATA_FILE = f"data_{st.session_state.user}.json"

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()

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

    if st.button("🏦 Add Account"):
        st.session_state.show_account_form = True

    if st.session_state.show_account_form:
        st.subheader("➕ Add Account")

        bank = st.selectbox("Select Bank", BANK_LIST)
        balance = st.number_input("Opening Balance", min_value=0.0)

        if st.button("Save Account"):
            if bank not in st.session_state.accounts:
                st.session_state.accounts.append(bank)
                st.session_state.account_balances[bank] = balance
                st.success(f"{bank} added with ₹{balance}")
                st.session_state.show_account_form = False
                st.rerun()
            else:
                st.warning("Already exists")

    if data:

        income = sum(d["amount"] for d in data if d["type"]=="Income")
        expense = sum(d["amount"] for d in data if d["type"]=="Expense")

        accounts = st.session_state.account_balances.copy()

        for d in data:
            acc = d.get("account","Cash")

            if acc not in accounts:
                accounts[acc] = 0

            if d["type"]=="Income":
                accounts[acc] += d["amount"]
            else:
                accounts[acc] -= d["amount"]

        balance = sum(accounts.values())

        st.markdown('<div class="card">', unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        c1.metric("Income", income)
        c2.metric("Expense", expense)
        c3.metric("Balance", balance)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🏦 Accounts")
        for a,b in accounts.items():
            st.write(f"{a}: ₹{b}")
        st.markdown('</div>', unsafe_allow_html=True)

        exp_data=[d for d in data if d["type"]=="Expense"]

        if exp_data:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            cat={}
            for d in exp_data:
                cat[d["category"]]=cat.get(d["category"],0)+d["amount"]
            fig,ax=plt.subplots()
            ax.pie(cat.values(),labels=cat.keys(),autopct="%1.1f%%")
            st.pyplot(fig)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        fig,ax=plt.subplots()
        ax.bar(["Income","Expense"],[income,expense])
        st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

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
            data.append({
                "type":t,
                "account":acc,
                "category":cat,
                "amount":amt,
                "date":str(date)
            })
            save_data(data)
            st.success("Added 🎉")
            st.rerun()