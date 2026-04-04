import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Advanced Data Dashboard", layout="wide")

st.title("📊 Advanced Data Explorer")
st.markdown("Upload and analyze multiple datasets with powerful insights")

# ---------------- MULTI FILE UPLOAD ----------------
uploaded_files = st.sidebar.file_uploader(
    "Upload CSV Files", type=["csv"], accept_multiple_files=True
)

if "files" not in st.session_state:
    st.session_state.files = {}

for file in uploaded_files:
    if file.name not in st.session_state.files:
        st.session_state.files[file.name] = pd.read_csv(file)

file_names = list(st.session_state.files.keys())

# ---------------- LANDING PAGE ----------------
if not file_names:
    st.markdown("## 👋 Welcome!")
    st.info("Upload one or more CSV files from the sidebar to start analysis.")
    st.stop()

# ---------------- FILE SELECT ----------------
selected_file = st.sidebar.selectbox("Select File", file_names)
df = st.session_state.files[selected_file]

st.sidebar.success(f"Active File: {selected_file}")

# ---------------- SEARCH + FILTER ----------------
st.sidebar.markdown("### 🔍 Filters")

search = st.sidebar.text_input("Search keyword")
if search:
    df = df[df.astype(str).apply(lambda row: row.str.contains(search, case=False).any(), axis=1)]

for col in df.select_dtypes(include='object').columns:
    vals = st.sidebar.multiselect(f"{col}", df[col].dropna().unique())
    if vals:
        df = df[df[col].isin(vals)]

sort_col = st.sidebar.selectbox("Sort By", df.columns)
df = df.sort_values(by=sort_col)

# ---------------- TABS ----------------
tabs = st.tabs([
    "📊 Overview", "🗂 Schema", "📈 Stats", "📋 Preview",
    "📉 Charts", "🧹 Data Quality", "📊 Advanced", "📤 Export"
])

# ---------------- OVERVIEW ----------------
with tabs[0]:
    file_size = st.session_state.files[selected_file].memory_usage().sum() / 1024**2
    mem = df.memory_usage(deep=True).sum() / 1024**2

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("File Size (MB)", f"{file_size:.2f}")
    c4.metric("Memory Usage (MB)", f"{mem:.2f}")

# ---------------- SCHEMA ----------------
with tabs[1]:
    schema = pd.DataFrame({
        "Column": df.columns,
        "Type": df.dtypes.astype(str),
        "Non-Null": df.count(),
        "Null": df.isnull().sum()
    })
    st.dataframe(schema)

# ---------------- STATS ----------------
with tabs[2]:
    st.write(df.describe())

# ---------------- PREVIEW ----------------
with tabs[3]:
    st.dataframe(df)

# ---------------- CHARTS ----------------
with tabs[4]:
    st.subheader("📊 Business Insights Dashboard")

    # Clean data ONCE
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

    # 1. Histogram
    if "CONTRACT AMOUNT" in df.columns:
        fig1 = px.histogram(df, x="CONTRACT AMOUNT", title="Contract Amount Distribution")
        st.plotly_chart(fig1)

    # 2. Owner chart
    if "Opportunity Owner_Name" in df.columns:
        top_owner = df["Opportunity Owner_Name"].value_counts().head(10)
        fig2 = px.bar(x=top_owner.index, y=top_owner.values, title="Top Owners")
        st.plotly_chart(fig2)

    # 3. Pie
    if "B2C / B2B__" in df.columns:
        fig3 = px.pie(df, names="B2C / B2B__", title="B2B vs B2C")
        st.plotly_chart(fig3)

    # 4. Revenue Trend (FIXED)
    if "Close Date" in df.columns and "CONTRACT AMOUNT" in df.columns:

        clean_df = df.dropna(subset=["Close Date", "CONTRACT AMOUNT"])

        if not clean_df.empty:
            trend = clean_df.groupby(
                clean_df["Close Date"].dt.to_period("M")
            )["CONTRACT AMOUNT"].sum().reset_index()

            trend["Close Date"] = trend["Close Date"].astype(str)

            fig4 = px.line(
                trend.tail(12),
                x="Close Date",
                y="CONTRACT AMOUNT",
                markers=True,
                title="Monthly Revenue Trend"
            )

            st.plotly_chart(fig4)

# ---------------- ADVANCED ----------------
with tabs[6]:
    st.subheader("Advanced Analysis")

    num_cols = df.select_dtypes(include='number').columns

    if len(num_cols) > 0:
        fig = px.box(df, y=num_cols[0])
        st.plotly_chart(fig)

# ---------------- EXPORT ----------------
with tabs[7]:
    st.download_button("Download CSV", df.to_csv().encode(), "data.csv")