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

# ---------------- CHARTS ----------------
with tabs[1]:

    st.subheader("🎯 Select Columns")
    num_cols = df.select_dtypes(include='number').columns.tolist()

    selected_cols = st.multiselect(
        "Choose numeric columns",
        num_cols,
        default=num_cols[:2]
    )

    # Histogram
    if selected_cols:
        col = st.selectbox("Histogram Column", selected_cols)
        fig = px.histogram(df, x=col, title=f"Distribution of {col}")
        fig.update_layout(xaxis_title=col, yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    # Box Plot
    if selected_cols:
        col2 = st.selectbox("Box Plot Column", selected_cols, key="box")
        fig2 = px.box(df, y=col2, title=f"Outliers in {col2}")
        st.plotly_chart(fig2, use_container_width=True)

    # Scatter Plot
    if len(selected_cols) >= 2:
        x_col = st.selectbox("X-axis", selected_cols, key="x")
        y_col = st.selectbox("Y-axis", selected_cols, key="y")

        fig3 = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
        st.plotly_chart(fig3, use_container_width=True)

    # Revenue Trend
    if "Close Date" in df.columns and "CONTRACT AMOUNT" in df.columns:

        clean_df = df.dropna(subset=["Close Date", "CONTRACT AMOUNT"])

        if not clean_df.empty:
            trend = clean_df.groupby(
                clean_df["Close Date"].dt.to_period("M")
            )["CONTRACT AMOUNT"].sum().reset_index()

            trend["Close Date"] = trend["Close Date"].astype(str)

            fig4 = px.line(
                trend,
                x="Close Date",
                y="CONTRACT AMOUNT",
                markers=True,
                title="📈 Monthly Revenue Trend"
            )

            fig4.update_layout(
                xaxis_title="Month",
                yaxis_title="Total Revenue"
            )

            st.plotly_chart(fig4, use_container_width=True)

# ---------------- ADVANCED ----------------
with tabs[2]:
    st.subheader("Advanced Insights")

    fig, ax = plt.subplots()
    sns.heatmap(df.isnull(), cbar=False)
    st.pyplot(fig)

# ---------------- EXPORT ----------------
with tabs[3]:
    st.download_button("Download Data", df.to_csv().encode(), "clean_data.csv")