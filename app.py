import streamlit as st
import pandas as pd
import plotly.express as px

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
        values = st.sidebar.multiselect(f"Filter {col}", df[col].dropna().unique())
        if values:
            df = df[df[col].isin(values)]

else:
    df = None

# ---------------- MAIN ----------------
if df is not None:

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        ["📊 Overview", "🗂 Schema", "📈 Stats", "📋 Preview", "📉 Charts", "🧹 Data Quality", "⬇️ Export"]
    )

    # ---------------- TAB 1 ----------------
    with tab1:
        st.subheader("Dataset Overview")

        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", df.shape[0])
        col2.metric("Columns", df.shape[1])
        col3.metric("Missing Values", df.isnull().sum().sum())

        st.dataframe(df.head(), use_container_width=True)

    # ---------------- TAB 2 ----------------
    with tab2:
        st.subheader("Schema Explorer")

        schema_df = pd.DataFrame({
            "Column Name": df.columns,
            "Data Type": df.dtypes.astype(str),
            "Non-Null Count": df.count(),
            "Null Count": df.isnull().sum()
        })

        st.dataframe(schema_df, use_container_width=True)

    # ---------------- TAB 3 ----------------
    with tab3:
        st.subheader("Statistics Summary")

        # Gently find columns that are already numeric
        numeric_df = df.select_dtypes(include='number')

        st.write("### Numeric Columns")
        if not numeric_df.empty:
            st.write(numeric_df.describe())
        else:
            st.warning("No numeric columns detected")

        st.write("### Categorical Columns")
        for col in df.select_dtypes(include='object').columns:
            st.write(f"**{col}**")
            st.write(df[col].value_counts().head())

    # ---------------- TAB 4 ----------------
    with tab4:
        st.subheader("Data Preview & Filtering")

        temp_df = df.copy()
        search = st.text_input("Global Search")

        if search:
            temp_df = temp_df[temp_df.apply(
                lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1
            )]

        st.dataframe(temp_df, use_container_width=True)

    # ---------------- TAB 5 ----------------
    with tab5:
        st.subheader("Charts & Visualizations")

        df_plot = df.copy()

        # Clean numeric values safely
        for col in df_plot.columns:
            if df_plot[col].dtype == 'object':
                try:
                    # Remove commas (e.g., "1,000.50" -> "1000.50") and try converting
                    clean_col = df_plot[col].astype(str).str.replace(',', '')
                    df_plot[col] = pd.to_numeric(clean_col)
                except ValueError:
                    # If it fails, it's a real text column (like Names/Cities). Leave it alone!
                    pass 

        numeric_cols = df_plot.select_dtypes(include='number').columns
        
        # Changed to > 0 so columns with a single constant number don't get thrown out
        valid_plot_cols = [c for c in numeric_cols if df_plot[c].dropna().nunique() > 0]

        if valid_plot_cols:

            plot_col = st.selectbox("Select column for Box Plot", valid_plot_cols)

            fig = px.box(df_plot, y=plot_col)
            st.plotly_chart(fig, use_container_width=True)

            # Insights
            st.write("### Insights")
            st.write(f"Mean: {df_plot[plot_col].mean():.2f}")
            st.write(f"Median: {df_plot[plot_col].median():.2f}")

            # Scatter
            st.write("### Compare Two Variables")
            if len(valid_plot_cols) >= 2:
                col_x = st.selectbox("X-axis", valid_plot_cols)
                col_y = st.selectbox("Y-axis", valid_plot_cols, index=1)

                fig_scatter = px.scatter(df_plot, x=col_x, y=col_y)
                st.plotly_chart(fig_scatter, use_container_width=True)

            # Correlation
            st.write("### Correlation Matrix")
            # Calculate correlation only on valid numeric columns
            corr = df_plot[valid_plot_cols].corr()
            fig_corr = px.imshow(corr, text_auto=True)
            st.plotly_chart(fig_corr, use_container_width=True)

        else:
            st.error("No numeric data detected after cleaning. Ensure your numbers aren't formatted with special characters (like $ or €) without cleaning them first.")

    # ---------------- TAB 6 ----------------
    with tab6:
        st.subheader("Data Quality Report")

        st.write(f"Duplicates: {df.duplicated().sum()}")

        null_cols = df.columns[df.isnull().all()]
        if len(null_cols) > 0:
            st.warning(f"Empty Columns: {list(null_cols)}")

            if st.button("Drop Empty Columns"):
                # Updates the session state dataframe and refreshes the app
                st.session_state.files[selected_file] = df.drop(columns=null_cols)
                st.success("Empty columns dropped!")
                st.rerun()
        else:
            st.success("No completely empty columns found.")

    # ---------------- TAB 7 ----------------
    with tab7:
        st.subheader("Download Data")

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "data_export.csv")

# ---------------- LANDING ----------------
else:
    st.markdown("""
## 👋 Welcome to Data Explorer Dashboard

Upload your dataset to:
- 📊 Analyze trends  
- 🔍 Explore patterns  
- 📈 Visualize insights  

Start by uploading a CSV file from the sidebar.
""")