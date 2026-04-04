import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Salesforce Audit Dashboard", layout="wide")

st.title("📊 Salesforce Account Audit Dashboard")

# ---------------- FILE UPLOAD ----------------
uploaded_files = st.sidebar.file_uploader(
    "Upload CSV Files", type=["csv"], accept_multiple_files=True
)

if "files" not in st.session_state:
    st.session_state.files = {}

for file in uploaded_files:
    if file.name not in st.session_state.files:
        st.session_state.files[file.name] = pd.read_csv(file)

file_names = list(st.session_state.files.keys())

if not file_names:
    st.info("Upload a CSV file to start")
    st.stop()

selected_file = st.sidebar.selectbox("Select File", file_names)
df = st.session_state.files[selected_file]

# ---------------- CLEANING ----------------
if "Close Date" in df.columns:
    df["Close Date"] = pd.to_datetime(df["Close Date"], errors='coerce')

if "CONTRACT AMOUNT" in df.columns:
    df["CONTRACT AMOUNT"] = (
        df["CONTRACT AMOUNT"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    df["CONTRACT AMOUNT"] = pd.to_numeric(df["CONTRACT AMOUNT"], errors='coerce')

# ---------------- SIDEBAR FILTER ----------------
search = st.sidebar.text_input("Search")
if search:
    df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False).any(), axis=1)]

# ---------------- TABS ----------------
tabs = st.tabs([
    "📊 Overview", "📈 Charts", "📊 Advanced", "📤 Export"
])

# ---------------- OVERVIEW ----------------
with tabs[0]:
    st.subheader("📌 Key Metrics")

    total_revenue = df["CONTRACT AMOUNT"].sum() if "CONTRACT AMOUNT" in df.columns else 0
    avg_deal = df["CONTRACT AMOUNT"].mean() if "CONTRACT AMOUNT" in df.columns else 0
    total_deals = len(df)

    latest_revenue = 0
    if "Close Date" in df.columns:
        latest_month = df["Close Date"].max()
        latest_revenue = df[df["Close Date"].dt.month == latest_month.month]["CONTRACT AMOUNT"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Revenue", f"{total_revenue:,.0f}")
    c2.metric("Avg Deal Size", f"{avg_deal:,.0f}")
    c3.metric("Total Deals", total_deals)
    c4.metric("Latest Month Revenue", f"{latest_revenue:,.0f}")

st.subheader("📊 Clean Business Insights")

# -------- SAFE COPY --------
clean_df = df.copy()

# -------- CLEAN DATE --------
if "Close Date" in clean_df.columns:
    clean_df["Close Date"] = pd.to_datetime(clean_df["Close Date"], errors="coerce")

# -------- CLEAN CONTRACT AMOUNT --------
if "CONTRACT AMOUNT" in clean_df.columns:
    clean_df["CONTRACT AMOUNT"] = (
        clean_df["CONTRACT AMOUNT"]
        .astype(str)
        .str.replace(r"[^\d.]", "", regex=True)  # removes everything except numbers
    )
    clean_df["CONTRACT AMOUNT"] = pd.to_numeric(clean_df["CONTRACT AMOUNT"], errors="coerce")

# -------- DROP BAD DATA --------
clean_df = clean_df.dropna(subset=["Close Date", "CONTRACT AMOUNT"])

# -------- DEBUG (IMPORTANT) --------
st.write("Rows after cleaning:", clean_df.shape[0])

# -------- STOP IF EMPTY --------
if clean_df.empty:
    st.error("No usable data — your dataset is messy")
else:

    # -------- KPI --------
    st.subheader("📌 Key Metrics")

    c1, c2 = st.columns(2)
    c1.metric("Total Revenue", f"{clean_df['CONTRACT AMOUNT'].sum():,.0f}")
    c2.metric("Total Deals", clean_df.shape[0])

    # -------- MONTHLY TREND --------
    st.subheader("📈 Monthly Revenue Trend")

    trend = clean_df.groupby(
        clean_df["Close Date"].dt.to_period("M")
    )["CONTRACT AMOUNT"].sum().reset_index()

    trend["Close Date"] = trend["Close Date"].astype(str)

    fig = px.line(
        trend,
        x="Close Date",
        y="CONTRACT AMOUNT",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Revenue"
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------- SIMPLE HISTOGRAM --------
    st.subheader("📊 Deal Size Distribution")

    fig2 = px.histogram(clean_df, x="CONTRACT AMOUNT")

    fig2.update_layout(
        xaxis_title="Contract Amount",
        yaxis_title="Number of Deals"
    )

    st.plotly_chart(fig2, use_container_width=True)
# ---------------- ADVANCED ----------------
with tabs[2]:
    st.subheader("Advanced Insights")

    fig, ax = plt.subplots()
    sns.heatmap(df.isnull(), cbar=False)
    st.pyplot(fig)

# ---------------- EXPORT ----------------
with tabs[3]:
    st.download_button("Download Data", df.to_csv().encode(), "clean_data.csv")