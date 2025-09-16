# tools/gtrends_analyzer/trends_monitor_cli.py

# import libraries
import os
import datetime
import argparse
import pandas as pd
from trends_tool import get_iot, get_rq

def chunk_keywords(keywords: list[str], chunk_size: int = 5) -> list[list[str]]:
    """
    Splits a list of keywords into chunks of a specified size.
    """
    return [keywords[i:i + chunk_size] for i in range(0, len(keywords), chunk_size)]

def main():
    """
    Main function to run the Google Trends Analyzer with CLI arguments.
    """
    # Argument Parser Setup
    parser = argparse.ArgumentParser(description="A tool to analyze Google Trends data for market research.")
    parser.add_argument('-k', '--keywords', nargs='+', required=True, help="List of keywords to analyze.")
    parser.add_argument('-m', '--mode', type = str, default = 'both', choices=['iot', 'rq', 'both'], 
                        help="The analysis mode to run.")
    parser.add_argument('-t', '--timeframe', type = str, default = 'today 12-m', 
                        help = "The timeframe for the analysis (see comment below for acceptable input formatting).")    
    """ Specify desired time frame for search. Acceptable formats are:
        * 'all' will show everything (all trend data)
        * Specific date range can be entered in the format 'YYYY-MM-DD YYYY-MM-DD' (e.g. '2025-09-08 2025-01-01')
        * Specific datetime range can be entered in the format 'YYYY-MM-DDTHH YYYY-MM-DDTHH' (e.g. '2025-09-08T12 2025-01-01T00')\n"\
        * Current time minus time pattern (recent_time past_time):
           * By month (only works for 1, 3, or 12 months) (e.g. past 3 months is 'today 3-m')
           * Daily (only works for 1 or 7 days) (e.g. past week is 'now 7-d')
           * Hourly (only works for 1 or 4 hours) (e.g. past 4 hours is 'now 4-H')
    """
    parser.add_argument('--report', action="store_true", help="Add this argument to print RQ console report.")
    args = parser.parse_args()

    # Use parsed arguments as inputs
    keywords = args.keywords
    mode_choice = args.mode
    timeframe = args.timeframe
    console_report = args.report

    # Begin Program
    print("\n--- Google Trends Market Analyzer ---\n")
    print(f"Keywords: {keywords}\n")
    print(f"Mode: {mode_choice} | Timeframe: {timeframe}\n")

    #timeframe = input("Enter timeframe (Default is today 12-m): ").strip()
    timeframe = timeframe.strip()
    print("")
    if not timeframe: timeframe = 'today 12-m'

    # Initialize data variables
    iot_data = None
    rq_data = None
    all_iot_data = pd.DataFrame()
    output_dir = os.path.join("..", "..", "downloads", "gtrends_reports")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Fetch data based on selected modality
    if mode_choice in ['iot', 'both']:
        print("--- Starting Interest Over Time Batch Processing ---\n")
        # Break keywords into chunks of 5 or less
        keyword_chunks = chunk_keywords(keywords)
        print(f"Found {len(keywords)} keywords, processing in {len(keyword_chunks)} batches.\n")

        for i, chunk in enumerate(keyword_chunks):
            print(f"Processing batch {i+1}/{len(keyword_chunks)}: {chunk}")
            iot_chunk_data = get_iot(chunk, timeframe=timeframe)

            if iot_chunk_data is not None:
                if all_iot_data.empty:
                    # Set empty DataFrame to first chunk data
                    all_iot_data = iot_chunk_data
                else:
                    # Merge new chunk's data with the main DataFrame
                    all_iot_data = all_iot_data.join(iot_chunk_data, how="outer")
        
        if not all_iot_data.empty: iot_data = all_iot_data

    if mode_choice in ['rq', 'both']:
        print("--- Starting Related Queries Batch Processing ---\n")
        # Pass full list since get_rq already processes one keyword at a time
        rq_data = get_rq(keywords, timeframe=timeframe)

    # Output 1: CSV export
    # IOT data
    if iot_data is not None:
        iot_filename = os.path.join(output_dir, f"iot_data_{timestamp}.csv")
        iot_data.to_csv(iot_filename)
        print(f"Saved Interest Over Time data to '{iot_filename}'\n")
    
    # RQ data
    if rq_data:
        print("Consolidating and saving Related Queries data to CSV...\n")

        # Create empty lists to hold individual DataFrames
        all_top_dfs = []
        all_rising_dfs = []

        # Loop through RQ data
        for keyword, data in rq_data.items():
            # 'Top' RQ data
            top_df = data.get('top')
            if top_df is not None:
                # Add a column for the original keyword
                top_df['Original Keyword'] = keyword
                all_top_dfs.append(top_df)
            
            # 'Rising' RQ data
            rising_df = data.get('rising')
            if rising_df is not None:
                # Add a column for the original keyword
                rising_df['Original Keyword'] = keyword
                all_rising_dfs.append(rising_df)

        # Consolidate the lists into two master DataFrames
        if all_top_dfs:
            master_top_df = pd.concat(all_top_dfs, ignore_index=True)
            top_filename = os.path.join(output_dir, f"rq_top_ALL_{timestamp}.csv")
            master_top_df.to_csv(top_filename, index=False) # index=False is cleaner
            print(f"- Saved all 'Top' queries to '{top_filename}'\n")

        if all_rising_dfs:
            master_rising_df = pd.concat(all_rising_dfs, ignore_index=True)
            rising_filename = os.path.join(output_dir, f"rq_rising_ALL_{timestamp}.csv")
            master_rising_df.to_csv(rising_filename, index=False)
            print(f"- Saved all 'Rising' queries to '{rising_filename}'\n")

    # Output 2: Console report for RQ
    if rq_data and console_report:
        print("--- Related Queries Report ---\n")
        for keyword, data in rq_data.items():
            print(f"--- For keyword: '{keyword}' ---\n")
            if data.get('top') is not None:
                print("--- Top Related Queries ---")
                print(f"{data.get('top').to_string()}\n")
            else:
                print("No top queries data found.\n")

            if data.get('rising') is not None:
                print("--- Rising Related Queries---")
                print(f"{data.get('rising').to_string()}\n")
            else:
                print("No rising queries data found.\n")

    print("--- Analysis Complete ---\n")


if __name__ == "__main__":
    main()