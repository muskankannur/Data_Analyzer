import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Advanced Data Dashboard", layout="wide")
st.title("📊 Advanced Data Explorer")

# ---------------- CLEANING FUNCTION ----------------
def clean_data(df):
    df = df.copy()

    # Standardize missing values
    df = df.replace(
        ["", " ", "NA", "N/A", "null", "None", "-", "--"],
        pd.NA
    )

    # Trim text
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].astype(str).str.strip()

    # Drop empty columns
    df = df.dropna(axis=1, how='all')

    # Drop high missing columns
    df = df.loc[:, df.isnull().mean() < 0.9]

    # Smart numeric conversion (SAFE)
    for col in df.columns:
        if df[col].dtype == "object":

            temp = df[col].astype(str).str.replace(r"[^\d.-]", "", regex=True)

            numeric_count = pd.to_numeric(temp, errors='coerce').notna().sum()
            total_count = len(df[col])

            # Only convert if mostly numeric
            if total_count > 0 and (numeric_count / total_count) > 0.7:
                df[col] = pd.to_numeric(temp, errors='coerce')

    # Remove duplicates
    df = df.drop_duplicates()

    return df


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
    st.info("Upload CSV files to start")
    st.stop()

# ---------------- SELECT FILE ----------------
selected_file = st.sidebar.selectbox("Select File", file_names)
raw_df = st.session_state.files[selected_file]

# ---------------- CLEAN DATA ----------------
if "cleaned_df" not in st.session_state or st.session_state.get("last_file") != selected_file:
    st.session_state.cleaned_df = clean_data(raw_df)
    st.session_state.last_file = selected_file

df = st.session_state.cleaned_df

st.sidebar.success(f"Active File: {selected_file}")

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
    c1.metric("Original Rows", raw_df.shape[0])
    c2.metric("Cleaned Rows", df.shape[0])
    c3.metric("Columns Removed", raw_df.shape[1] - df.shape[1])

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

        # Outliers
        q1 = temp[selected_col].quantile(0.25)
        q3 = temp[selected_col].quantile(0.75)
        iqr = q3 - q1

        outliers = temp[
            (temp[selected_col] < q1 - 1.5 * iqr) |
            (temp[selected_col] > q3 + 1.5 * iqr)
        ]

        st.write(f"Outliers: {len(outliers)}")

        # Heatmap
        if len(num_cols) >= 2:
            st.markdown("### Correlation Heatmap")

            selected_cols = st.multiselect(
                "Select columns",
                num_cols,
                default=num_cols[:5]
            )

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