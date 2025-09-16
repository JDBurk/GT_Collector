# tools/gtrends_analyzer/trends_monitor.py

# import libraries
import os
import datetime
import matplotlib.pyplot as plt
import pandas as pd
from trends_tool import get_iot, get_rq

def plot_iot(df, keywords, filename):
    """
    Plots the Interest Over Time DataFrame and saves it to a file.
    """
    # Create MPL figure (width, height [in inches])
    plt.figure(figsize=(12, 6))

    # Plot each keyword's trend line
    for keyword in keywords:
        if keyword in df.columns:
            plt.plot(df.index, df[keyword], label=keyword)

    # Add titles and labels for clarity
    plt.title("Google Trends: Interest Over Time")
    plt.xlabel("Date")
    plt.ylabel("Relative Interest")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()  # Adjusts the plot layout to prevent label overlapping
    
    # Save the plot to the specified file
    plt.savefig(filename)
    print(f"Chart saved successfully to '{filename}'\n")

def chunk_keywords(keywords: list[str], chunk_size: int = 5) -> list[list[str]]:
    """
    Splits a list of keywords into chunks of a specified size.
    """
    return [keywords[i:i + chunk_size] for i in range(0, len(keywords), chunk_size)]


def main():
    """
    Main function to run the script.
    """
    print("\n--- Google Trends Market Analyzer ---\n")

    # Mode selection
    while True:
        print("Please select an analysis mode:")
        print("1. Interest Over Time (IOT)")
        print("2. Related Queries (RQ)")
        print("3. Both IOT and RQ\n")
        #print("4. Exit")
        mode_choice = input("Enter your choice (1, 2, or 3): ").strip()
        if mode_choice in ['1', '2', '3']:
            print("")
            break
        else: print("\nInvalid choice. Please enter 1, 2, or 3.\n")

    # Get user input for keywords
    keywords_input = input("Enter keywords to analyze, separated by commas: ")
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    if not keywords:
        print("\nInvalid input. Exiting.\n")
        return
    
    # Specify desired time frame for search
    print("\n\nSpecify desired time frame for search. Acceptable formats are:\n"\
        "* 'all' will show everything (all trend data)\n"\
        "* Specific date range can be entered in the format 'YYYY-MM-DD YYYY-MM-DD' (e.g. '2025-09-08 2025-01-01')\n"\
        "* Specific datetime range can be entered in the format 'YYYY-MM-DDTHH YYYY-MM-DDTHH' (e.g. '2025-09-08T12 2025-01-01T00')\n"\
        "* Current time minus time pattern (recent_time past_time):\n"\
        "   * By month (only works for 1, 3, or 12 months) (e.g. past 3 months is 'today 3-m')\n"\
        "   * Daily (only works for 1 or 7 days) (e.g. past week is 'now 7-d')\n"\
        "   * Hourly (only works for 1 or 4 hours) (e.g. past 4 hours is 'now 4-H')\n"\
    )
    timeframe = input("Enter timeframe (Default is today 12-m): ").strip()
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
    if mode_choice in ['1', '3']:
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

    if mode_choice in ['2', '3']:
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

        """ [OLD CODE] Saves CSVs for each keyword separately
        for keyword, data in rq_data.items():
            safe_keyword = keyword.replace(" ", "_")
            if data.get('top') is not None:
                top_filename = os.path.join(output_dir, f"rq_top_{safe_keyword}_{timestamp}.csv")
                data['top'].to_csv(top_filename)
                print(f"- Saved top queries for '{keyword}' to '{top_filename}'\n")
            if data.get('rising') is not None:
                rising_filename = os.path.join(output_dir, f"rq_rising_{safe_keyword}_{timestamp}.csv")
                data['rising'].to_csv(rising_filename)
                print(f"- Saved rising queries for '{keyword}' to '{rising_filename}'\n")
        """
    
    # Output 2: Optional Plotting
    if iot_data is not None:
        plot_choice = input("Generate a plot of the IOT data? (y/n): ").strip().lower()
        #plot_name = input("Enter file name (timestamp is automatically appended): ").strip().lower()
        if plot_choice == 'y':   
            safe_query = "_".join(k.replace(" ", "_") for k in keywords)
            chart_filename = os.path.join(output_dir, f"iot_chart_{safe_query}_{timestamp}.png")
            plot_iot(iot_data, keywords, chart_filename)

    # Output 3: Console report for RQ
    if rq_data:
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
    elif mode_choice in ['2', '3']:
        print("Could not generate report. No Related Queries data was found.\n")

    print("--- Analysis Complete ---\n")


if __name__ == "__main__":
    main()