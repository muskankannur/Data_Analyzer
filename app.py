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

with tabs[4]:
    st.subheader("📊 Business Insights Dashboard")

    # Convert date
    if "Close Date" in df.columns:
        df["Close Date"] = pd.to_datetime(df["Close Date"], errors='coerce')

    # 1. Contract Distribution
    if "CONTRACT AMOUNT" in df.columns:
        st.subheader("💰 How Big Are Our Deals?")
        fig1 = px.histogram(df, x="CONTRACT AMOUNT", nbins=30,
                            title="Distribution of Contract Amount")
        st.plotly_chart(fig1, use_container_width=True)

    # 2. Owner Performance
    if "Opportunity Owner_Name" in df.columns:
        st.subheader("👩‍💼 Who Handles Most Opportunities?")
        top_owner = df["Opportunity Owner_Name"].value_counts().head(10)

        fig2 = px.bar(x=top_owner.index, y=top_owner.values,
                      title="Top 10 Opportunity Owners")
        st.plotly_chart(fig2, use_container_width=True)

    # 3. Business Type
    if "B2C / B2B__" in df.columns:
        st.subheader("🏢 Business Type Split")
        fig3 = px.pie(df, names="B2C / B2B__", title="B2B vs B2C")
        st.plotly_chart(fig3, use_container_width=True)

    # 4. Revenue Trend
    if "Close Date" in df.columns and "CONTRACT AMOUNT" in df.columns:
        st.subheader("📈 Revenue Trend")

        trend = df.groupby(df["Close Date"].dt.to_period("M"))["CONTRACT AMOUNT"].sum().reset_index()
        trend["Close Date"] = trend["Close Date"].astype(str)

        fig4 = px.line(trend, x="Close Date", y="CONTRACT AMOUNT",
                       title="Monthly Revenue Trend")
        st.plotly_chart(fig4, use_container_width=True)

    # 5. Outliers
    if "CONTRACT AMOUNT" in df.columns:
        st.subheader("⚠️ Outlier Detection")
        fig5 = px.box(df, y="CONTRACT AMOUNT",
                      title="Outliers in Contract Amount")
        st.plotly_chart(fig5, use_container_width=True)



# ---------------- ADVANCED VISUALS ----------------
with tabs[6]:
    st.subheader("📊 Advanced Data Analysis")

    # DEFINE numeric columns (FIX)
    num_cols = df.select_dtypes(include='number').columns

    # -------- 1. MISSING VALUE HEATMAP --------
    st.subheader("🧹 Missing Data Pattern")

    fig, ax = plt.subplots()
    sns.heatmap(df.isnull(), cbar=False)
    ax.set_title("Missing Values Heatmap")
    st.pyplot(fig)

    # -------- 2. CORRELATION MATRIX --------
    st.subheader("🔗 Relationship Between Numeric Features")

    if len(num_cols) > 1:
        fig, ax = plt.subplots()
        sns.heatmap(df[num_cols].corr(), annot=True, cmap="coolwarm")
        ax.set_title("Correlation Matrix")
        st.pyplot(fig)
    else:
        st.warning("Not enough numeric columns for correlation")

    # -------- 3. BOX PLOT (OUTLIERS) --------
    st.subheader("⚠️ Detect Outliers")

    if len(num_cols) > 0:
        col = st.selectbox("Select Column for Outlier Detection", num_cols)
        fig = px.box(df, y=col, title=f"Outliers in {col}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No numeric columns available")

# ---------------- EXPORT ----------------
with tabs[7]:
    schema_csv = schema.to_csv(index=False).encode()
    stats_csv = df.describe().to_csv().encode()

    st.download_button("Download Schema", schema_csv, "schema.csv")
    st.download_button("Download Stats", stats_csv, "stats.csv")