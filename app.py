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

    # ---------------- TAB 5 ----------------
    with tab5:
        st.subheader("Charts & Visualizations")

        # 1. CREATE A CLEAN COPY FOR PLOTTING
        df_plot = df.copy()

        # 🛠️ AUTO-CLEAN: Try to convert potential numeric columns that are stuck as 'object'
        for col in df_plot.columns:
            if df_plot[col].dtype == 'object':
                # Check if the column looks like currency or numbers with commas
                # We strip $, commas, and whitespace
                test_clean = df_plot[col].astype(str).str.replace(r'[^\d.-]', '', regex=True)
                converted = pd.to_numeric(test_clean, errors='coerce')
                
                # If at least 50% of the column successfully converted to numbers, keep it!
                if converted.notnull().sum() > (len(df_plot) * 0.5):
                    df_plot[col] = converted

        # 2. IDENTIFY VALID COLUMNS
        all_cols = df_plot.columns.tolist()
        numeric_cols = df_plot.select_dtypes(include='number').columns.tolist()

        if all_cols:
            st.write("### Compare Two Variables")
            col_x = st.selectbox("X-axis (Select Contract Amount)", all_cols, 
                                 index=all_cols.index("CONTRACT AMOUNT") if "CONTRACT AMOUNT" in all_cols else 0)
            col_y = st.selectbox("Y-axis (Select SEO Manager)", all_cols, 
                                 index=all_cols.index("SEO MANAGER w/ STRATEGIST") if "SEO MANAGER w/ STRATEGIST" in all_cols else 0)

            # 🔍 DIAGNOSTIC CHECK
            if df_plot[col_x].dtype == 'object' and df_plot[col_y].dtype == 'object':
                st.error(f"⚠️ Both '{col_x}' and '{col_y}' are currently Text (Categorical). Scatter plots need at least one numeric column to show data points.")
            else:
                # 3. RENDER CHART
                try:
                    fig_scatter = px.scatter(
                        df_plot, 
                        x=col_x, 
                        y=col_y, 
                        color=col_y if df_plot[col_y].dtype == 'object' else None,
                        title=f"{col_x} vs {col_y}",
                        template="plotly_white"
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                except Exception as e:
                    st.error(f"Error rendering chart: {e}")

            # 4. DATA HEALTH CHECK (Visible in Tab)
            with st.expander("View Data Types for these columns"):
                st.write(f"**{col_x} Type:** {df_plot[col_x].dtype}")
                st.write(f"**{col_y} Type:** {df_plot[col_y].dtype}")
                st.write(f"**Empty Rows in {col_x}:** {df_plot[col_x].isnull().sum()}")
                st.write(f"**Empty Rows in {col_y}:** {df_plot[col_y].isnull().sum()}")

        else:
            st.error("No data available to plot.")
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