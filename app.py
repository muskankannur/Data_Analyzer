import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Data Dashboard", layout="wide")

st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 24px;
    color: #4CAF50;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("📊 Data Explorer Dashboard")
st.markdown("Upload a CSV file and explore data insights interactively")

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

# ---------------- FILE SELECTION ----------------
if file_names:
    selected_file = st.sidebar.selectbox("Select File", file_names)
    df = st.session_state.files[selected_file]
    st.sidebar.success(f"Active File: {selected_file}")

    # ✅ Sidebar Filters
    st.sidebar.write("### Filters")
    for col in df.select_dtypes(include='object').columns:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) < 50: # Only show filter if manageable
            values = st.sidebar.multiselect(f"Filter {col}", unique_vals)
            if values:
                df = df[df[col].isin(values)]
else:
    df = None

# ---------------- MAIN ----------------
if df is not None:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        ["📊 Overview", "🗂 Schema", "📈 Stats", "📋 Preview", "📉 Charts", "🧹 Data Quality", "⬇️ Export"]
    )

    # --- TAB 1: OVERVIEW ---
    with tab1:
        st.subheader("Dataset Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", df.shape[0])
        col2.metric("Columns", df.shape[1])
        col3.metric("Missing Values", df.isnull().sum().sum())
        st.dataframe(df.head(), use_container_width=True)

    # --- TAB 2: SCHEMA ---
    with tab2:
        st.subheader("Schema Explorer")
        schema_df = pd.DataFrame({
            "Column Name": df.columns,
            "Data Type": df.dtypes.astype(str),
            "Non-Null Count": df.count(),
            "Null Count": df.isnull().sum()
        })
        st.dataframe(schema_df, use_container_width=True)

    # --- TAB 3: STATS ---
    with tab3:
        st.subheader("Statistics Summary")
        num_cols = df.select_dtypes(include='number')
        if not num_cols.empty:
            st.write("### Numeric Columns")
            st.write(num_cols.describe())
        else:
            st.warning("No numeric columns detected. Go to 'Charts' to try forcing a cleanup.")

    # --- TAB 5: CHARTS (With enhanced cleaning) ---
    with tab5:
        st.subheader("Charts & Visualizations")
        
        # --- ENHANCED CLEANING UTILITY ---
        with st.expander("🛠 Advanced Data Cleaning (Fix Numeric Issues)"):
            st.info("If your numbers contain symbols like $, %, or commas, select them below to convert them to numbers.")
            cols_to_fix = st.multiselect("Select columns to force into numeric:", df.columns)
            
            if st.button("Clean Selected Columns"):
                for col in cols_to_fix:
                    # Remove characters that aren't digits, dots, or minus signs
                    df[col] = df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                st.session_state.files[selected_file] = df
                st.success("Columns cleaned! Refreshing...")
                st.rerun()

        # Identify numeric columns for plotting
        numeric_cols = df.select_dtypes(include='number').columns
        
        if len(numeric_cols) > 0:
            plot_col = st.selectbox("Select column for Box Plot", numeric_cols)
            fig = px.box(df, y=plot_col, points="all", title=f"Distribution of {plot_col}")
            st.plotly_chart(fig, use_container_width=True)

            if len(numeric_cols) >= 2:
                st.write("### Compare Two Variables")
                col_x = st.selectbox("X-axis", numeric_cols, index=0)
                col_y = st.selectbox("Y-axis", numeric_cols, index=min(1, len(numeric_cols)-1))
                fig_scatter = px.scatter(df, x=col_x, y=col_y, trendline="ols")
                st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.error("No numeric data detected. Use the cleaning tool above to fix columns.")

    # --- TAB 6: QUALITY ---
    with tab6:
        st.subheader("Data Quality")
        st.write(f"**Duplicate Rows:** {df.duplicated().sum()}")
        null_counts = df.isnull().sum()
        st.write("**Missing Values per Column:**")
        st.write(null_counts[null_counts > 0])

    # --- TAB 7: EXPORT ---
    with tab7:
        st.subheader("Download Data")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, f"cleaned_{selected_file}")

else:
    st.markdown("### 👋 Please upload a CSV file from the sidebar to begin.")