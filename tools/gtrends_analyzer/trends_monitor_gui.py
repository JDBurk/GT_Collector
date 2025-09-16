####################################################################################################
# tools/gtrends_analyzer/trends_monitor_gui.py
# LAST UPDATED: 25-09-13
#
# Ideas for added functionality:
# 0) Build "proper" front-end with Flask/ FastAPI
# 1) Export directly to CSV, XLSX, Google Docs, etc (OR add option to select preferred format)
# 2) Import list of 
#
# Design
# 0) Customize elements (colors, dividers, Markdown, etc)
# 1) 
#
####################################################################################################

# --- import libraries ---
import os
import datetime
import streamlit as st
import pandas as pd
from trends_tool import get_iot, get_rq
from io import BytesIO

# ==================================================
# Initialize Session State
# ==================================================
# Runs once at session start, create placeholders for data
if 'data_fetched' not in st.session_state:
    st.session_state.data_fetched = False
if 'iot_data' not in st.session_state:
    st.session_state.iot_data = None
if 'rq_data' not in st.session_state:
    st.session_state.rq_data = None
if 'last_keywords' not in st.session_state:
    st.session_state.last_keywords = None
if 'keywords_input' not in st.session_state:
    st.session_state.keywords_input = "flare jeans, graphic tees, leather boots"

# ==================================================
# Helper functions
# ==================================================
# --------------------------------------------------
# Helper function to manage keyword chunk sizes 
# --------------------------------------------------
def chunk_keywords(keywords: list[str], chunk_size: int = 5) -> list[list[str]]:
    """
    Splits a list of keywords into chunks of a specified size.
    """
    return [keywords[i:i + chunk_size] for i in range(0, len(keywords), chunk_size)]

# --------------------------------------------------
# Helper function for export to XLSX
# --------------------------------------------------
def save_to_xlsx(iot_df: pd.DataFrame | None, rq_data: dict | None) -> bytes:
    """
    #Takes IOT and RQ data and writes them to separate sheets in an in-memory Excel file.

    #Args:
        #iot_df (pd.DataFrame | None): The Interest Over Time (IOT) DataFrame.
        #rq_data (dict | None): The Related Queries (RQ) data (dictionary).

    #Returns:
        #bytes: The content of the .xlsx file as bytes.
    """
    # Create in-memory buffer
    output = BytesIO()

    # Use pandas ExcelWriter to write to the buffer
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Write the IOT data to its own sheet if it exists
        if iot_df is not None:
            iot_df.to_excel(writer, sheet_name='Interest Over Time')
        # Consolidate and write RQ data to its own sheet if it exists
        if rq_data:
            all_top_dfs, all_rising_dfs = [], []
            for keyword, data in rq_data.items():
                # Top Related Queries
                top_df = data.get('top')
                if top_df is not None:
                    top_df['Original Keyword'] = keyword
                    all_top_dfs.append(top_df)
                # Rising Related Queries
                rising_df = data.get('rising')
                if rising_df is not None:
                    rising_df['Original Keyword'] = keyword
                    all_rising_dfs.append(rising_df)
            if all_top_dfs:
                master_top_df = pd.concat(all_top_dfs, ignore_index=True)
                master_top_df.to_excel(writer, sheet_name='Top_Related_Queries', index=False)
            if all_rising_dfs:
                master_rising_df = pd.concat(all_rising_dfs, ignore_index=True)
                master_rising_df.to_excel(writer, sheet_name='Rising_Related_Queries', index=False)
    
    # Get the content of the buffer and return it
    processed_data = output.getvalue()
    return processed_data

# --------------------------------------------------
# Helper function for Data Retrieval
# --------------------------------------------------
def fetch_data(keywords, mode_choice, selected_timeframe):
    """
    Handles data fetching process and updates session state.
    NOTE: Use st.status for real-time, expandable feedback
    """
    # --- Retrieve and process IOT Data ---
    with st.status("Fetching Interest Over Time data...", expanded=True) as status_iot:
        if mode_choice in ['Both', 'Interest Over Time Only']:
            keyword_chunks = chunk_keywords(keywords)
            if len(keyword_chunks) == 1:
                st.write(f"Processing {len(keywords)} keyword(s)....")
            else:
                st.write(f"Processing {len(keywords)} keywords in {len(keyword_chunks)} batches....")
            all_iot_data = pd.DataFrame()
            for chunk in keyword_chunks:
                iot_chunk_data = get_iot(chunk, timeframe=selected_timeframe)
                if iot_chunk_data is not None:
                    if all_iot_data.empty:
                        all_iot_data = iot_chunk_data
                    else:
                        all_iot_data = all_iot_data.join(iot_chunk_data, how="outer")
            if not all_iot_data.empty: 
                st.session_state.iot_data = all_iot_data    # Store final DataFrame
                status_iot.update(label="IOT data retrieval succeeded!", state="complete")
            else:
                st.session_state.iot_data = None
                status_iot.update(label="IOT data retrieval failed.", state="error")
        else:
            st.session_state.iot_data = None
            status_iot.update(label="IOT data skipped.", state="complete")

    # --- Retrieve and process RQ Data ---
    with st.status("Fetching Related Queries data...", expanded=True) as status_rq:
        if mode_choice in ['Both', 'Related Queries Only']:
            st.write(f"Processing {len(keywords)} keyword(s)....")
            st.session_state.rq_data = get_rq(keywords, timeframe=selected_timeframe)
            if st.session_state.rq_data:
                status_rq.update(label="RQ data retrieved succeeded!", state="complete")
            else:
                status_rq.update(label="RQ data retrieval failed.", state="error")
        else:
            st.session_state.rq_data = None
            status_rq.update(label="RQ data skipped.", state="complete")

    st.session_state.data_fetched = True    # Flag that data has been successfully collected
    st.session_state.last_keywords = keywords   # Remember search keywords

# ==================================================
# Callback functions
# ==================================================
# --- Process uploaded CSV or XLSX files ---
def process_uploaded_file():
    """
    Reads the uploaded file from session state and updates the keywords_input state.
    """
    uploaded_file = st.session_state.uploader_key   # Get the file from session state
    if uploaded_file is not None:
        try:
            # If file extension is .CSV
            if uploaded_file.name.endswith('.csv'):
                # Read the CSV into a pandas DataFrame
                df = pd.read_csv(uploaded_file)
            # If file extension is .XLSX
            elif uploaded_file.name.endswith('.xlsx'):
                # Read the XLSX into a pandas DataFrame
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            # Check if the DataFrame is not empty and has at least one column
            if not df.empty and len(df.columns) > 0:
                keywords_from_file = df.iloc[:, 0].dropna().tolist()
                # Hack - update the other widget's state variable
                st.session_state.keywords_input = ', '.join(map(str, keywords_from_file))
        
        # General exception handling
        except Exception as e:
            st.error(f"An error occurred while processing the uploaded file: {e}")

# ==================================================
# Section - App Splash Page & User Inputs
# ==================================================
# --- Title and info elements ---
st.title("Google Trends Market Analyzer")
st.info("This tool fetches and analyzes Google Trends data to provide market insights.")

# --- User Input 1 - KEYWORDS ---
# ----- Keyword input header
st.header("1. Enter Your Keywords")

# ----- Keyword input element
keywords_input = st.text_input(
    "Enter keywords to analyze, separated by commas:",
    key='keywords_input'
)

# ----- File Uploader element
uploaded_file = st.file_uploader(
    "Or, upload a one-column CSV or XLSX keyword file:",
    type=['csv','xlsx'],
    key = 'uploader_key',
    on_change = process_uploaded_file
)

# --- User Input 2 - ANALYSIS AND TIMEFRAME SELECTION ---
# ----- Select analysis options header
st.header("2. Select Analysis Options")
# ----- Create 2 columns for cleaner layout (one for analysis mode, one for timeframe)
col1, col2 = st.columns(2)  

# ----- Analysis Mode Selectbox
with col1:
    mode_choice = st.selectbox(
        "Analysis Mode:",
        ('Both', 'Interest Over Time Only', 'Related Queries Only'),
        key='mode'
    )

# ----- Timeframe selectbox
with col2:
    timeframe_option = st.selectbox(
        "Timeframe",
        ('All time', 'Last 5 years',
         'Last 12 months', 'Last 3 months', 'Last month',
         'Last 7 days', 'Last 24 hours', 'Last 4 hours', 'Last hour',
         'Custom Date Range'
        ),
        key='timeframe'
    )

# ------- Timeframe selectbox - Conditionally display date inputs if 'Custom Date Range' is selected
if timeframe_option == 'Custom Date Range':
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input("Start date", datetime.date.today() - datetime.timedelta(days=365))
    with date_col2:
        end_date = st.date_input("End date", datetime.date.today())

# ----- Map user-friendly names to the API's required format
timeframe_map = {
    'All time': 'all', 'Last 5 years': 'today 5-y',
    'Last 12 months': 'today 12-m', 'Last 3 months': 'today 3-m',
    'Last month': 'today 1-m', 'Last 7 days': 'now 7-d',
    'Last 24 hours': 'now 1-d', 'Last 4 hours': 'now 4-H',
    'Last hour': 'now 1-H'
}

# ==================================================
# Section - Analysis & Reset Buttons
# ==================================================
# --- Create Button Objects ---
col_btn1, col_btn2 = st.columns(2)

# --- Run Analysis Button ---
with col_btn1:
    if st.button("Run Analysis"):
        # Format keywords (only when needed for analysis)
        keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
        if not keywords:
            st.error("Please enter at least one keyword.")
        else:
            # Reset IOT and RQ data from previous session(s)
            st.session_state.iot_data = None
            st.session_state.rq_data = None

            # Determine the correct timeframe string to use for the API call
            if timeframe_option == 'Custom Date Range':
                if start_date > end_date:
                    st.error("Error: Start date cannot be after end date.")
                    st.stop()
                # Format for pytrends: 'YYYY-MM-DD YYYY-MM-DD'
                selected_timeframe = f"{start_date.strftime('%Y-%m-%d')} {end_date.strftime('%Y-%m-%d')}"
            else:
                selected_timeframe = timeframe_map[timeframe_option]

            # Call data retrieval function
            fetch_data(keywords, mode_choice, selected_timeframe)
            st.success("Data collection complete!")

# --- Reset Button ---
with col_btn2:
    if st.button("Reset"):
        st.session_state.data_fetched = False
        st.session_state.iot_data = None
        st.session_state.rq_data = None
        st.session_state.last_keywords = None
        st.rerun()

# ==================================================
# Section - Display & Save Results
# ==================================================
# --- Display Results after data has been retrieved ---
if st.session_state.data_fetched:
    # --- Section headers
    st.header("Analysis Results")
    st.markdown(f"#**Showing Results for:** '{', '.join(st.session_state.last_keywords)}'")
    
    # --- Create 2 column layout for Results Section
    results_col, status_col = st.columns([2,1])

    # --- Subsection - Results (Left Pane) ---
    with results_col:
        # --- Display IOT Data
        if st.session_state.iot_data is not None:
            st.subheader("Interest Over Time (IOT)")
            st.line_chart(st.session_state.iot_data)
            with st.expander("View Raw IOT Data"):
                st.dataframe(st.session_state.iot_data)
                # --- Download IOT Data CSV ---
                #iot_csv = st.session_state.iot_data.to_csv().encode('utf-8')
                #st.download_button(
                    #label = "Download IOT Data as CSV", 
                    #data = iot_csv, 
                    #file_name=f'iot_data_{timestamp}.csv',
                    #mime = 'text/csv'
                #)
        
        # --- Display RQ Data
        if st.session_state.rq_data is not None:
            st.subheader("Related Queries (RQ)")
            for keyword, data in st.session_state.rq_data.items():
                with st.expander(f"View RQ Raw Data for: '{keyword}'"):
                    top_df, rising_df = data.get('top'), data.get('rising')
                    if top_df is not None:
                        st.markdown("## Top Related Queries")
                        st.dataframe(top_df)
                    if rising_df is not None:
                        st.markdown("## Rising Related Queries")
                        st.dataframe(rising_df)
    
    # --- Subsection - Download Report [Confusion abound here - want to cut AI Studio sessions before 250K Tokens]
    with status_col:
        st.subheader("Download Report")

        # --- XLSX Download Button ---
        # ----- Generate data variables before button (IOT, RQ, timestamp)
        xlsx_data = save_to_xlsx(st.session_state.iot_data, st.session_state.rq_data)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # ----- Create Button
        st.download_button(
            label = "Download Full Report as XLSX",
            data = xlsx_data,
            file_name = f"full_report_{timestamp}.xlsx",
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        # --- Visual Speparator
        #st.markdown("---")
