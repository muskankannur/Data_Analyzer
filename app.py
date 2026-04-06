import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import snowflake.connector

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Advanced Data Dashboard", layout="wide")
st.title("📊 Advanced Data Explorer")

# ---------------- SNOWFLAKE CONFIG ----------------
SNOWFLAKE_CONFIG = {
    'user': 'YOUR_USERNAME',
    'password': 'YOUR_PASSWORD',
    'account': 'YOUR_ACCOUNT',       # e.g., xy12345.us-east-1
    'warehouse': 'YOUR_WAREHOUSE',
    'database': 'SALES_DB',
    'schema': 'PUBLIC'
}

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cur = conn.cursor()
    cur.execute("SELECT * FROM SALESFORCE_DATA")
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=columns)

df = load_data()
st.sidebar.success(f"Active Table: SALESFORCE_DATA")

# ---------------- CLEANING FUNCTION ----------------
def clean_data(df):
    df = df.copy()
    df = df.replace(["", " ", "NA", "N/A", "null", "None", "-", "--"], pd.NA)
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()
    df = df.dropna(axis=1, how='all')
    df = df.loc[:, df.isnull().mean() < 0.9]
    for col in df.columns:
        if df[col].dtype == "object":
            temp = df[col].astype(str).str.replace(r"[^\d.-]", "", regex=True)
            numeric_count = pd.to_numeric(temp, errors='coerce').notna().sum()
            total_count = len(df[col])
            if total_count > 0 and (numeric_count / total_count) > 0.7:
                df[col] = pd.to_numeric(temp, errors='coerce')
    df = df.drop_duplicates()
    return df

# ---------------- CLEAN DATA ----------------
df = clean_data(df)

# ---------------- SEARCH ----------------
search = st.sidebar.text_input("Search")
if search:
    df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False).any(), axis=1)]

# ---------------- TABS ----------------
tabs = st.tabs([
    "📊 Overview", "🗂 Schema", "📈 Stats", "📋 Preview",
    "📉 Charts", "🧹 Data Report", "📊 Advanced", "📤 Export"
])

# ---------------- OVERVIEW ----------------
with tabs[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", df.shape[0])
    c2.metric("Columns", df.shape[1])
    c3.metric("Missing Values", df.isnull().sum().sum())

# ---------------- SCHEMA ----------------
with tabs[1]:
    schema = pd.DataFrame({
        "Column": df.columns,
        "Type": df.dtypes.astype(str),
        "Nulls": df.isnull().sum()
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
    st.subheader("Charts")
    num_cols = df.select_dtypes(include='number').columns.tolist()
    if num_cols:
        selected_col = st.selectbox("Select Column", num_cols)
        temp = df.dropna(subset=[selected_col])
        st.metric("Total", f"{temp[selected_col].sum():,.0f}")
        st.plotly_chart(px.histogram(temp, x=selected_col), use_container_width=True)
        st.plotly_chart(px.box(temp, y=selected_col), use_container_width=True)
    else:
        st.warning("No numeric columns available")

# ---------------- DATA REPORT ----------------
with tabs[5]:
    st.subheader("🧹 Data Cleaning Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Original Rows", df.shape[0])
    c2.metric("Cleaned Rows", df.shape[0])
    c3.metric("Columns Removed", 0)
    st.write("Missing Values After Cleaning")
    st.write(df.isnull().sum())

# ---------------- ADVANCED ----------------
with tabs[6]:
    st.subheader("Advanced Analysis")
    num_cols = df.select_dtypes(include='number').columns.tolist()
    if num_cols:
        selected_col = st.selectbox("Column for Analysis", num_cols)
        temp = df.dropna(subset=[selected_col])
        st.write(temp[selected_col].describe())
        q1 = temp[selected_col].quantile(0.25)
        q3 = temp[selected_col].quantile(0.75)
        iqr = q3 - q1
        outliers = temp[(temp[selected_col] < q1 - 1.5 * iqr) | (temp[selected_col] > q3 + 1.5 * iqr)]
        st.write(f"Outliers: {len(outliers)}")
        if len(num_cols) >= 2:
            st.markdown("### Correlation Heatmap")
            selected_cols = st.multiselect("Select columns", num_cols, default=num_cols[:5])
            if len(selected_cols) >= 2:
                corr = df[selected_cols].corr()
                fig, ax = plt.subplots(figsize=(8, 5))
                sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
                st.pyplot(fig)

# ---------------- EXPORT ----------------
with tabs[7]:
    st.subheader("Export Cleaned Data")
    st.dataframe(df.head())
    file_format = st.selectbox("Format", ["CSV", "Excel"])
    file_name = st.text_input("File Name", "clean_data")
    if file_format == "CSV":
        data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data, f"{file_name}.csv")
    else:
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("Download Excel", buffer.getvalue(), f"{file_name}.xlsx")