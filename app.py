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

# ---------------- SEARCH FILTER ----------------
search = st.sidebar.text_input("Search")
if search:
    df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False).any(), axis=1)]

# ---------------- TABS ----------------
tabs = st.tabs([
    "📊 Overview", "🗂 Schema", "📈 Stats", "📋 Preview",
    "📉 Charts", "🧹 Data Quality", "📊 Advanced", "📤 Export"
])

# ---------------- OVERVIEW ----------------
with tabs[0]:
    st.subheader("📌 Key Metrics")

    temp_df = df.copy()

    if "CONTRACT AMOUNT" in temp_df.columns:
        temp_df["CONTRACT AMOUNT"] = (
            temp_df["CONTRACT AMOUNT"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True)
        )
        temp_df["CONTRACT AMOUNT"] = pd.to_numeric(temp_df["CONTRACT AMOUNT"], errors='coerce')

    total_revenue = temp_df["CONTRACT AMOUNT"].sum() if "CONTRACT AMOUNT" in temp_df.columns else 0
    avg_deal = temp_df["CONTRACT AMOUNT"].mean() if "CONTRACT AMOUNT" in temp_df.columns else 0
    total_deals = len(temp_df)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"{total_revenue:,.0f}")
    c2.metric("Avg Deal Size", f"{avg_deal:,.0f}")
    c3.metric("Total Deals", total_deals)

# ---------------- SCHEMA ----------------
with tabs[1]:
    st.dataframe(pd.DataFrame({
        "Column": df.columns,
        "Type": df.dtypes.astype(str),
        "Nulls": df.isnull().sum()
    }))

# ---------------- STATS ----------------
with tabs[2]:
    st.write(df.describe())

# ---------------- PREVIEW ----------------
with tabs[3]:
    st.dataframe(df)

# ---------------- CHARTS ----------------
with tabs[4]:
    st.subheader("📊 Business Insights")

    clean_df = df.copy()

    # Clean Date
    if "Close Date" in clean_df.columns:
        clean_df["Close Date"] = pd.to_datetime(clean_df["Close Date"], errors="coerce")

    # Clean Amount
    if "CONTRACT AMOUNT" in clean_df.columns:
        clean_df["CONTRACT AMOUNT"] = (
            clean_df["CONTRACT AMOUNT"]
            .astype(str)
            .str.replace(r"[^\d.]", "", regex=True)
        )
        clean_df["CONTRACT AMOUNT"] = pd.to_numeric(clean_df["CONTRACT AMOUNT"], errors="coerce")

    clean_df = clean_df.dropna(subset=["Close Date", "CONTRACT AMOUNT"])

    if clean_df.empty:
        st.error("No valid data after cleaning")
    else:

        # KPI
        c1, c2 = st.columns(2)
        c1.metric("Revenue", f"{clean_df['CONTRACT AMOUNT'].sum():,.0f}")
        c2.metric("Deals", clean_df.shape[0])

        # Monthly Trend
        st.subheader("📈 Monthly Revenue Trend")

        trend = clean_df.groupby(
            clean_df["Close Date"].dt.to_period("M")
        )["CONTRACT AMOUNT"].sum().reset_index()

        trend["Close Date"] = trend["Close Date"].astype(str)

        fig = px.line(trend, x="Close Date", y="CONTRACT AMOUNT", markers=True)
        fig.update_layout(xaxis_title="Month", yaxis_title="Revenue")

        st.plotly_chart(fig, use_container_width=True)

        # Histogram
        st.subheader("📊 Deal Size Distribution")

        fig2 = px.histogram(clean_df, x="CONTRACT AMOUNT")
        st.plotly_chart(fig2, use_container_width=True)

# ---------------- DATA QUALITY ----------------
with tabs[5]:
    st.subheader("Missing Values")
    st.write(df.isnull().sum())

# ---------------- ADVANCED ----------------
with tabs[6]:
    st.subheader("Advanced Analysis")

    fig, ax = plt.subplots()
    sns.heatmap(df.isnull(), cbar=False)
    st.pyplot(fig)

# ---------------- EXPORT ----------------
with tabs[7]:
    st.download_button("Download CSV", df.to_csv().encode(), "data.csv")