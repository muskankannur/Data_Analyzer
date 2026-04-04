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

# ---------------- CLEANED DF STATE ----------------
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = df.copy()

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

# ---------------- DATA QUALITY ----------------
with tabs[5]:
    st.subheader("🧹 Data Quality Analysis")

    working_df = st.session_state.cleaned_df

    # Missing Values
    st.markdown("### Missing Values")
    st.write(working_df.isnull().sum())

    # Empty Columns
    empty_cols = working_df.columns[working_df.isnull().all()].tolist()
    st.markdown("### Empty Columns")
    st.write(empty_cols)

    if st.button("Drop Empty Columns"):
        working_df = working_df.drop(columns=empty_cols)
        st.session_state.cleaned_df = working_df
        st.success("Empty columns removed")

    # Duplicates
    st.markdown("### Duplicate Rows")
    dup_count = working_df.duplicated().sum()
    st.write(f"Total Duplicates: {dup_count}")

    if st.button("Remove Duplicates"):
        working_df = working_df.drop_duplicates()
        st.session_state.cleaned_df = working_df
        st.success("Duplicates removed")

# ---------------- CHARTS ----------------
with tabs[4]:
    st.subheader("📊 Business Insights Dashboard")

    clean_df = st.session_state.cleaned_df.copy()

    # Date cleaning
    if "Close Date" in clean_df.columns:
        clean_df["Close Date"] = pd.to_datetime(clean_df["Close Date"], errors='coerce')

    # Numeric cleaning
    for col in clean_df.columns:
        if clean_df[col].dtype == "object":
            cleaned = clean_df[col].astype(str).str.replace(r"[^\d.]", "", regex=True)
            clean_df[col] = pd.to_numeric(cleaned, errors="coerce")

    # Select numeric column
    num_cols = clean_df.select_dtypes(include='number').columns.tolist()

    if not num_cols:
        st.error("No numeric columns found")
    else:
        selected_col = st.selectbox("Select Column", num_cols)

        # Drop only necessary nulls
        required_cols = [selected_col]
        if "Close Date" in clean_df.columns:
            required_cols.append("Close Date")

        clean_df = clean_df.dropna(subset=required_cols)

        if clean_df.empty:
            st.error("No valid data after cleaning")
        else:
            st.metric("Total", f"{clean_df[selected_col].sum():,.0f}")

            fig1 = px.histogram(clean_df, x=selected_col)
            st.plotly_chart(fig1)

            fig2 = px.box(clean_df, y=selected_col)
            st.plotly_chart(fig2)

            if "Close Date" in clean_df.columns:
                trend = clean_df.groupby(
                    clean_df["Close Date"].dt.to_period("M")
                )[selected_col].sum().reset_index()

                trend["Close Date"] = trend["Close Date"].astype(str)

                fig3 = px.line(trend, x="Close Date", y=selected_col)
                st.plotly_chart(fig3)

with tabs[6]:
    st.subheader("📊 Advanced Data Analysis")

    adv_df = st.session_state.cleaned_df.copy()

    # -------- CLEAN NUMERIC DATA --------
    for col in adv_df.columns:
        if adv_df[col].dtype == "object":
            cleaned = adv_df[col].astype(str).str.replace(r"[^\d.]", "", regex=True)
            adv_df[col] = pd.to_numeric(cleaned, errors="coerce")

    num_cols = adv_df.select_dtypes(include='number').columns.tolist()

    if not num_cols:
        st.error("No numeric data available")
    else:

        # -------- COLUMN SELECT --------
        selected_col = st.selectbox("Select Column for Analysis", num_cols)

        adv_df = adv_df.dropna(subset=[selected_col])

        if adv_df.empty:
            st.error("No valid data after cleaning")

        else:
            # ---------------- SUMMARY STATS ----------------
            st.markdown("### 📌 Statistical Summary")

            st.write(adv_df[selected_col].describe())

            # ---------------- OUTLIER DETECTION ----------------
            st.markdown("### 🚨 Outlier Detection")

            q1 = adv_df[selected_col].quantile(0.25)
            q3 = adv_df[selected_col].quantile(0.75)
            iqr = q3 - q1

            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            outliers = adv_df[
                (adv_df[selected_col] < lower) |
                (adv_df[selected_col] > upper)
            ]

            st.write(f"Outliers Count: {len(outliers)}")

            # ---------------- SKEWNESS ----------------
            st.markdown("### 📊 Distribution Shape")

            skew = adv_df[selected_col].skew()

            if skew > 1:
                st.warning("Highly Right Skewed (Most values are low, few very high)")
            elif skew < -1:
                st.warning("Highly Left Skewed (Most values are high, few very low)")
            else:
                st.success("Fairly Normal Distribution")

            # ---------------- TOP CORRELATIONS ----------------
            st.markdown("### 🔗 Strong Correlations")

            corr = adv_df[num_cols].corr()[selected_col].drop(selected_col)

            strong_corr = corr[abs(corr) > 0.5].sort_values(ascending=False)

            if strong_corr.empty:
                st.info("No strong correlations found")
            else:
                st.write(strong_corr)

            # ---------------- INSIGHT ----------------
            st.markdown("### 🧠 Auto Insight")

            mean_val = adv_df[selected_col].mean()

            st.write(f"""
            - Average value is **{mean_val:,.2f}**
            - Total records analyzed: **{len(adv_df)}**
            - Data spread suggests variability in business performance
            """)