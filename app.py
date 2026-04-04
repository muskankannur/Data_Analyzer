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

# Store files
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

# Sorting
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

    def highlight(val):
        if "int" in val or "float" in val:
            return "background-color: lightgreen"
        elif "object" in val:
            return "background-color: lightblue"
        else:
            return ""

    st.dataframe(schema.style.applymap(highlight, subset=["Type"]))

# ---------------- STATS ----------------
with tabs[2]:
    st.subheader("Numeric Summary")
    st.write(df.describe())

    st.subheader("Top Categorical Values")
    for col in df.select_dtypes(include='object').columns:
        st.write(f"**{col}**")
        st.write(df[col].value_counts().head())

    st.subheader("Missing %")
    st.write((df.isnull().sum() / len(df)) * 100)

# ---------------- PREVIEW ----------------
with tabs[3]:
    st.dataframe(df, use_container_width=True)

# ---------------- BASIC CHARTS ----------------
with tabs[4]:
    num_cols = df.select_dtypes(include='number').columns
    cat_cols = df.select_dtypes(include='object').columns

    if len(num_cols) > 0:
        col = st.selectbox("Numeric Column", num_cols)
        fig = px.histogram(df, x=col)
        st.plotly_chart(fig, use_container_width=True)

    if len(cat_cols) > 0:
        col = st.selectbox("Categorical Column", cat_cols, key="cat")
        top = df[col].value_counts().head(10)
        fig = px.bar(x=top.index, y=top.values)
        st.plotly_chart(fig, use_container_width=True)

# ---------------- DATA QUALITY ----------------
with tabs[5]:
    st.subheader("Duplicates")
    dup = df[df.duplicated()]
    st.write(f"Duplicate Rows: {dup.shape[0]}")
    if not dup.empty:
        st.dataframe(dup)

    st.subheader("All Null Columns")
    null_cols = df.columns[df.isnull().all()]
    st.write(null_cols)

    st.subheader("High Cardinality Columns")
    high_card = [col for col in df.columns if df[col].nunique() > 50]
    st.write(high_card)

# ---------------- ADVANCED VISUALS ----------------
with tabs[6]:
    st.subheader("Missing Value Heatmap")
    fig, ax = plt.subplots()
    sns.heatmap(df.isnull(), cbar=False)
    st.pyplot(fig)

    st.subheader("Correlation Matrix")
    num_df = df.select_dtypes(include='number')
    if not num_df.empty:
        fig, ax = plt.subplots()
        sns.heatmap(num_df.corr(), annot=True)
        st.pyplot(fig)

    st.subheader("Box Plot")
    if len(num_cols) > 0:
        col = st.selectbox("Column for Box Plot", num_cols, key="box")
        fig = px.box(df, y=col)
        st.plotly_chart(fig)

# ---------------- EXPORT ----------------
with tabs[7]:
    schema_csv = schema.to_csv(index=False).encode()
    stats_csv = df.describe().to_csv().encode()

    st.download_button("Download Schema", schema_csv, "schema.csv")
    st.download_button("Download Stats", stats_csv, "stats.csv")