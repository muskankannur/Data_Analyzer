import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Advanced Data Dashboard", layout="wide")

st.title("📊 Advanced Data Explorer")

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
df = st.session_state.files[selected_file]

# ---------------- CLEANED DF ----------------
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = df.copy()

st.sidebar.success(f"Active File: {selected_file}")

# ---------------- FILTERS ----------------
search = st.sidebar.text_input("Search")

if search:
    df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False).any(), axis=1)]

for col in df.select_dtypes(include='object').columns:
    vals = st.sidebar.multiselect(col, df[col].dropna().unique())
    if vals:
        df = df[df[col].isin(vals)]

# ---------------- TABS ----------------
tabs = st.tabs([
    "📊 Overview", "🗂 Schema", "📈 Stats", "📋 Preview",
    "📉 Charts", "🧹 Data Quality", "📊 Advanced", "📤 Export"
])

# ---------------- OVERVIEW ----------------
with tabs[0]:
    st.metric("Rows", df.shape[0])
    st.metric("Columns", df.shape[1])

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

# ---------------- DATA QUALITY ----------------
with tabs[5]:
    st.subheader("Data Cleaning")

    working_df = st.session_state.cleaned_df

    st.write("Missing Values")
    st.write(working_df.isnull().sum())

    empty_cols = working_df.columns[working_df.isnull().all()].tolist()
    st.write("Empty Columns:", empty_cols)

    if st.button("Drop Empty Columns"):
        st.session_state.cleaned_df = working_df.drop(columns=empty_cols)
        st.rerun()

    dup = working_df.duplicated().sum()
    st.write(f"Duplicates: {dup}")

    if st.button("Remove Duplicates"):
        st.session_state.cleaned_df = working_df.drop_duplicates()
        st.rerun()

# ---------------- CHARTS ----------------
with tabs[4]:
    st.subheader("Charts")

    clean_df = st.session_state.cleaned_df.copy()

    # Convert numeric
    for col in clean_df.columns:
        if clean_df[col].dtype == "object":
            clean_df[col] = pd.to_numeric(
                clean_df[col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )

    num_cols = clean_df.select_dtypes(include='number').columns.tolist()

    if num_cols:
        selected_col = st.selectbox("Select Column", num_cols)

        clean_df = clean_df.dropna(subset=[selected_col])

        st.metric("Total", f"{clean_df[selected_col].sum():,.0f}")

        st.plotly_chart(px.histogram(clean_df, x=selected_col))
        st.plotly_chart(px.box(clean_df, y=selected_col))

# ---------------- ADVANCED ----------------
with tabs[6]:
    st.subheader("Advanced Analysis")

    adv_df = st.session_state.cleaned_df.copy()

    for col in adv_df.columns:
        if adv_df[col].dtype == "object":
            adv_df[col] = pd.to_numeric(
                adv_df[col].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )

    num_cols = adv_df.select_dtypes(include='number').columns.tolist()

    if num_cols:
        selected_col = st.selectbox("Column for Analysis", num_cols)

        adv_df = adv_df.dropna(subset=[selected_col])

        st.write(adv_df[selected_col].describe())

        # Outliers
        q1 = adv_df[selected_col].quantile(0.25)
        q3 = adv_df[selected_col].quantile(0.75)
        iqr = q3 - q1

        outliers = adv_df[
            (adv_df[selected_col] < q1 - 1.5 * iqr) |
            (adv_df[selected_col] > q3 + 1.5 * iqr)
        ]

        st.write(f"Outliers: {len(outliers)}")

        # Correlation Heatmap
        st.markdown("### Correlation Heatmap")

        if len(num_cols) >= 2:
            selected_cols = st.multiselect(
                "Select columns",
                num_cols,
                default=num_cols[:5]
            )

            if len(selected_cols) >= 2:
                corr = adv_df[selected_cols].corr()

                fig, ax = plt.subplots(figsize=(8, 5))
                sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
                st.pyplot(fig)

# ---------------- EXPORT ----------------
with tabs[7]:
    st.subheader("Export Data")

    export_df = st.session_state.cleaned_df

    st.dataframe(export_df.head())

    file_format = st.selectbox("Format", ["CSV", "Excel"])
    file_name = st.text_input("File Name", "clean_data")

    if file_format == "CSV":
        data = export_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data, f"{file_name}.csv")

    else:
        from io import BytesIO
        buffer = BytesIO()

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, index=False)

        st.download_button("Download Excel", buffer.getvalue(), f"{file_name}.xlsx")