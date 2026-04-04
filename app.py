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

# ---------------- INITIAL CLEAN COPY ----------------
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = df.copy()

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

    temp_df = st.session_state.cleaned_df.copy()

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

# ---------------- DATA QUALITY ----------------
with tabs[5]:
    st.subheader("🧹 Data Cleaning Controls")

    working_df = st.session_state.cleaned_df

    # EMPTY COLUMNS
    empty_cols = working_df.columns[working_df.isnull().all()].tolist()
    st.write("Empty Columns:", empty_cols)

    if st.button("Drop Empty Columns"):
        working_df = working_df.drop(columns=empty_cols)
        st.session_state.cleaned_df = working_df
        st.success("Empty columns removed")

    # DUPLICATES
    dup_count = working_df.duplicated().sum()
    st.write(f"Duplicate Rows: {dup_count}")

    if st.button("Remove Duplicates"):
        working_df = working_df.drop_duplicates()
        st.session_state.cleaned_df = working_df
        st.success("Duplicates removed")

    # MISSING
    st.write("Missing Values:")
    st.write(working_df.isnull().sum())

with tabs[4]:
    st.subheader("📊 Business Insights")

    clean_df = st.session_state.cleaned_df.copy()

    # -------- DATE CLEANING --------
    if "Close Date" in clean_df.columns:
        clean_df["Close Date"] = pd.to_datetime(clean_df["Close Date"], errors="coerce")

    # -------- NUMERIC CLEANING --------
    for col in clean_df.columns:
        if clean_df[col].dtype == "object":
            cleaned = (
                clean_df[col]
                .astype(str)
                .str.replace(r"[^\d.]", "", regex=True)
            )
            clean_df[col] = pd.to_numeric(cleaned, errors="coerce")

    # -------- SELECT NUMERIC COLUMNS --------
    num_cols = clean_df.select_dtypes(include='number').columns.tolist()

    if not num_cols:
        st.error("No numeric columns available for analysis")
        st.stop()

    selected_col = st.selectbox("Select Column for Analysis", num_cols)

    # -------- DROP ONLY IMPORTANT NULLS --------
    required_cols = [selected_col]

    if "Close Date" in clean_df.columns:
        required_cols.append("Close Date")

    clean_df = clean_df.dropna(subset=required_cols)

    # -------- FINAL CHECK --------
    if clean_df.empty:
        st.error("No valid data after filtering (your column is mostly empty)")
    else:
        # KPI
        st.metric("Total Value", f"{clean_df[selected_col].sum():,.0f}")

        # HISTOGRAM
        fig1 = px.histogram(clean_df, x=selected_col,
                            title=f"{selected_col} Distribution")
        st.plotly_chart(fig1, use_container_width=True)

        # BOX
        fig2 = px.box(clean_df, y=selected_col,
                      title=f"{selected_col} Outliers")
        st.plotly_chart(fig2, use_container_width=True)

        # TREND
        if "Close Date" in clean_df.columns:
            trend = clean_df.groupby(
                clean_df["Close Date"].dt.to_period("M")
            )[selected_col].sum().reset_index()

            trend["Close Date"] = trend["Close Date"].astype(str)

            fig3 = px.line(
                trend,
                x="Close Date",
                y=selected_col,
                markers=True,
                title=f"Monthly Trend of {selected_col}"
            )

            st.plotly_chart(fig3, use_container_width=True)

# ---------------- ADVANCED ----------------
with tabs[6]:
    st.subheader("Advanced Analysis")

    fig, ax = plt.subplots()
    sns.heatmap(df.isnull(), cbar=False)
    st.pyplot(fig)

# ---------------- EXPORT ----------------
with tabs[7]:
    st.download_button("Download CSV", st.session_state.cleaned_df.to_csv().encode(), "clean_data.csv")