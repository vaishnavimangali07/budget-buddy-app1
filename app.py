import streamlit as st
import json
import matplotlib.pyplot as plt
import datetime

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Budget Buddy", layout="centered")

# ======================================================
# 🌈 UI STYLING (APP STYLE)
# ======================================================
st.markdown("""
<style>

.main {
    background-color: #f4f6fb;
}

.block-container {
    max-width: 420px;
    padding-top: 1rem;
    margin: auto;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

div[data-testid="stMetric"] {
    background-color: white;
    border-radius: 15px;
    padding: 12px;
    box-shadow: 0 6px 15px rgba(0,0,0,0.08);
}

.stButton button {
    background-color: #2563eb;
    color: white;
    border-radius: 12px;
    width: 100%;
    padding: 8px;
}

[data-testid="stSidebar"] {
    background-color: #ffffff;
}

h1, h2, h3 {
    text-align: center;
    color: #1d4ed8;
}

</style>
""", unsafe_allow_html=True)

# ======================================================
# 👤 AUTH SYSTEM (LOGIN + SIGNUP)
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

# SESSION STATE
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# ======================================================
# AUTH PAGE
# ======================================================
if not st.session_state.logged_in:

    st.title("💰 Budget Buddy")

    option = st.radio("Select Option", ["Login", "Create Account"])

    # -------- LOGIN --------
    if option == "Login":
        st.subheader("🔐 Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid credentials")

    # -------- SIGNUP --------
    else:
        st.subheader("🆕 Create Account")

        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Sign Up"):
            if new_user in users:
                st.warning("User already exists!")
            elif new_user == "" or new_pass == "":
                st.warning("Please fill all fields")
            else:
                users[new_user] = new_pass
                save_users(users)

                # AUTO LOGIN
                st.session_state.logged_in = True
                st.session_state.user = new_user

                st.success("Account created! 🎉")
                st.rerun()

    st.stop()

# ======================================================
# SIDEBAR
# ======================================================
st.sidebar.title(f"💰 {st.session_state.user}")

if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

page = st.sidebar.selectbox("Navigate", ["Dashboard", "Add Transaction"])

# ======================================================
# USER DATA FILE
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

    st.title("💰 Budget Buddy")

    months = ["All","January","February","March","April","May","June",
              "July","August","September","October","November","December"]

    selected_month = st.selectbox("📅 Select Month", months)

    filtered_data = data

    if selected_month != "All":
        filtered_data = [
            d for d in data
            if "date" in d and
            datetime.datetime.strptime(d["date"], "%Y-%m-%d").strftime("%B") == selected_month
        ]

    if filtered_data:

        income = sum(d["amount"] for d in filtered_data if d["type"] == "Income")
        expense = sum(d["amount"] for d in filtered_data if d["type"] == "Expense")
        balance = income - expense

        expense_data = [d for d in filtered_data if d["type"] == "Expense"]

        if expense > income:
            st.error(f"🚨 Overspending by ₹{expense - income}")
        elif expense == income:
            st.warning("⚠️ Income fully spent!")
        else:
            st.success(f"👍 Savings ₹{income - expense}")

        if income > 0 and expense >= 0.7 * income:
            st.warning(f"⚠️ You used {round((expense/income)*100)}% of income!")

        st.subheader("📅 Daily Spending Analysis")

        daily = {}
        for d in expense_data:
            daily[d["date"]] = daily.get(d["date"], 0) + d["amount"]

        if daily:
            fig, ax = plt.subplots()
            ax.plot(list(daily.keys()), list(daily.values()), marker="o")
            plt.xticks(rotation=45)
            st.pyplot(fig)

        st.subheader("🧠 Smart Insights")

        if expense_data:
            avg = sum(d["amount"] for d in expense_data) / len(expense_data)
            max_spend = max(daily.values()) if daily else 0

            if expense > income:
                st.error("🚨 Overspending detected!")
            elif expense > 0.8 * income:
                st.warning("⚠️ High spending!")
            elif avg > 500:
                st.info("💡 High daily spending")
            else:
                st.success("👍 Healthy spending")

            st.write(f"Avg Spend: ₹{avg:.2f}")
            st.write(f"Highest Day: ₹{max_spend}")

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Income", income)
        col2.metric("💸 Expense", expense)
        col3.metric("💰 Balance", balance)

        st.divider()

        st.subheader("📋 Transactions")

        for i, item in enumerate(filtered_data):
            col1, col2, col3, col4 = st.columns(4)

            col1.write(item["type"])
            col2.write(item["category"])
            col3.write(item["amount"])

            if col4.button("🗑️", key=i):
                data.remove(item)
                save_data(data)
                st.rerun()

        st.divider()

        st.subheader("📊 Expense Distribution")

        if expense_data:
            cat_sum = {}
            for d in expense_data:
                cat_sum[d["category"]] = cat_sum.get(d["category"], 0) + d["amount"]

            fig, ax = plt.subplots()
            ax.pie(cat_sum.values(), labels=cat_sum.keys(), autopct="%1.1f%%")
            st.pyplot(fig)

            top = max(cat_sum, key=cat_sum.get)
            st.success(f"🔥 Top Category: {top} → ₹{cat_sum[top]}")

        st.subheader("📈 Income vs Expense")

        fig, ax = plt.subplots()
        ax.bar(["Income", "Expense"], [income, expense])
        st.pyplot(fig)

    else:
        st.info("No transactions yet.")

# ======================================================
# ADD TRANSACTION
# ======================================================
else:

    st.title("➕ Add Transaction")

    t_type = st.selectbox("Type", ["Income", "Expense"])
    category = st.selectbox("Category", ["Food","Travel","Bills","Shopping","Salary","Other"])
    amount = st.number_input("Amount", min_value=0.0)
    date = st.date_input("Date", value=datetime.date.today())

    if st.button("Add"):

        data.append({
            "type": t_type,
            "category": category,
            "amount": amount,
            "date": str(date)
        })

        save_data(data)
        st.success("Transaction Added! 🎉")