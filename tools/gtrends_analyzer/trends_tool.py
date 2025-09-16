# tools/gtrends_analyzer/trends_tool.py

# import libraries
import time
import random
import os
import pandas as pd
from pytrends.request import TrendReq

# --- Add a standard browser User-Agent ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
}

""" Random Proxy list [NOT WORKING]
# Proxy list for rapid proxy cycling
PROXY_LIST = []
"""

# Residential proxy from Bright Data
#RES_PROXY = os.getenv("BD_PROXY_URL")

# Set function variables
delay_low = 20
delay_high = 45
max_retries = 3

def _get_pytrends_client() -> TrendReq:
    """
    Initializes and returns a TrendReq client with a random proxy.
    """
    """ Use random proxy from PROXY_LIST [NOT WORKING! LIKELY ISSUE WITH pytrends library]
    # Select a random proxy for each request
    proxy_ip = random.choice(PROXY_LIST)
    proxies = {'http': f"http://{proxy_ip}", 'https': f"https://{proxy_ip}"}
    print(f"Using proxy: http://{proxy_ip}")

    # Pass proxy to TrendReq for initialization
    # Using requests_args to pass headers, which pytrends will pass to requests.
    return TrendReq(hl='en-US', tz=300, timeout=(10,25), proxies=proxies,
                    #retries=2, backoff_factor=0.1,
                    #requests_args={'headers': HEADERS})
    """
    """ Use residential proxy from Bright Data [NOT WORKING EITHER]
    # Use Residential Proxy to (hopefully) avoid blocked access
    proxies = {'http': RES_PROXY, 'https': RES_PROXY}
    print(f"Using proxy: {RES_PROXY}")
    return TrendReq(hl='en-US', tz=300, timeout=(10,25), proxies=proxies, 
                    retries=2, backoff_factor=0.1,
                    requests_args={'headers': HEADERS})
    """

    # Initialize pytrends WITHOUT PROXY
    requests_args = {'headers': HEADERS} #, 'verify': False
    return TrendReq(hl='en-US', tz=300, timeout=(10,25), requests_args=requests_args)
    
 
def get_iot(keywords: list[str], timeframe: str = 'today 12-m') -> pd.DataFrame | None:
    """ Fetches Google Trends 'Interest Over Time' (IOT) data for a list of keywords.
    Keywords are processed one at a time with delays to avoid rate limiting or 429 errors.

    Args:
        keywords (list[str]): A list of keywords to search for.
        timeframe (str): The time range for the data (e.g., '', 'today 5-y').

    Returns:
        pd.DataFrame: A pandas DataFrame containing the trend daa, or None on failure

    Notes:
        * keywords
            * Keywords for query
            * MAX 5 terms per request
            * Use pytrends.suggestions() to automatically resolve narrowed search terms for requests
        * cat
            * Category to narrow down search
            * 0 = everything, see https://github.com/pat310/google-trends-api/wiki/Google-Trends-Categories for full list
        * geo
            * 2-letter country abbreviation, defaults to world
            * Use 'us' for united states, specify state by adding state abbreviation (e.g. 'US-AL' for Alabama)
        * tz
            * Timezone offset in minutes
            * '360' is US-CST (UTC-06:00), '300' is US-EST (UTC-05:00)
        * timeframe
            * Several formatting methods
                * Default is last 5 years // 'today 5-y'
                * Everything // 'all'
                * Specific dates // 'YYYY-MM-DD YYYY-MM-DD'
                * Specific datetimes // 'YYYY-MM-DDTHH YYYY-MM-DDTHH'
                * Current time minus time pattern
                    * By month (only works for 1, 3, or 12 months) // 'today 3-m'
                    * Daily (only works for 1 or 7 days) // 'now 7-d'
                    * Hourly (only works for 1 or 4 hours) // 'now 4-H'
        * grprop
            * Google property to filter by, defaults to web search
            * Other options include 'images', 'news', 'youtube', or 'froogle' (for Google Shopping)
    """
    all_trends = pd.DataFrame()
    
    for keyword in keywords:
        print(f"Fetching IOT data for: '{keyword}'...")
        for attempt in range(max_retries):
            try:
                # Add polite delay before each call
                time.sleep(random.uniform(delay_low, delay_high))

                pytrends = _get_pytrends_client()

                # Build the payload for the request & fetch the interest over time data
                pytrends.build_payload(kw_list=[keyword], cat=0, timeframe=timeframe, geo='US', gprop='')
                interest_df = pytrends.interest_over_time()

                if not interest_df.empty and keyword in interest_df.columns:
                    # Initialize the DataFrame on first keyword pass
                    if all_trends.empty:
                        all_trends = interest_df[[keyword]]
                    # Otherwise, merge new data in
                    else:
                        all_trends = all_trends.join(interest_df[[keyword]], how='outer')

            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed for '{keyword}': {e}")
                if attempt + 1 < max_retries:
                    print("Retrying...\n")
                else:
                    print(f"All retries failed for '{keyword}'. Skipping this keyword.\n")
            else:
                # Success: break out of the retry loop
                print(f"Successfully fetched data for '{keyword}'.\n")
                break
        else:
            # This block runs if the for loop completes without a `break` (i.e., all retries failed)
            continue
    
    # Drop the 'isPartial' column if it exists
    if 'isPartial' in all_trends.columns:
        all_trends.drop(columns=['isPartial'], inplace=True)
    return all_trends if not all_trends.empty else None

def get_rq(keywords: list[str], timeframe: str = 'today 12-m') -> dict[str, dict]:
    """ Fetches Google Trends 'Related Queries' (RQ) data for a list of keywords.
    Args:
        keywords (list[str]): The keywords to search for.
        timeframe (str): The time range for the data.
    
    Returns:
        dict: A dictionary where keys are keywords and values are another dictionary
              containing 'top' and 'rising' DataFrames, or None if no data is fetched.
    """
    all_rq ={}
    
    for keyword in keywords:
        print(f"Fetching RQ data for: '{keyword}'...")
        for attempt in range(max_retries):
            try:
                # Add polite delay before each call
                time.sleep(random.uniform(delay_low, delay_high))

                pytrends = _get_pytrends_client()
                
                # Build the payload for the request & fetch the related queries data
                pytrends.build_payload(kw_list=[keyword], timeframe=timeframe)
                rq_dict = pytrends.related_queries()

                # Extract the desired dataframes from the nested results.
                top_queries = rq_dict.get(keyword, {}).get('top')
                rising_queries = rq_dict.get(keyword, {}).get('rising')
                all_rq[keyword] = {'top': top_queries, 'rising': rising_queries}

            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed for '{keyword}': {e}")
                if attempt + 1 < max_retries:
                    print("Retrying...\n")
                else:
                    print(f"All retries failed for '{keyword}'. Skipping this keyword.\n")
            else:
                # Success: break out of the retry loop
                print(f"Successfully fetched data for '{keyword}'.\n")
                break
        else:
            # This block runs if the for loop completes without a `break` (i.e., all retries failed)
            continue
    
    return all_rq if all_rq else None

# TEST BLOCK
if __name__ == "__main__":
    
    # Test 1: Batch Interest Over Time [get_iot()]
    print("\n--- Testing Batch Interest Over Time ---\n")
    iot_keywords = ["boho dress","linen pants","wool coat"]
    print(f"Fetching IoT data for: {iot_keywords}\n")
    iot_data = get_iot(iot_keywords)
    
    if iot_data is not None and not iot_data.empty:
        print("\nSuccessfully fetched and merged IOT data. Here are the last 5 data rows: \n")
        print(f"{iot_data.tail()}\n")
        print(f"Final DataFrame has {len(iot_data.columns)} columns: {list(iot_data.columns)}\n")
        #print(f"Final DataFrame has {len(iot_data.columns)} columns and {iot_data.rows} rows.\n")
        # Extra check for DataFrame shape
        #print(f"DataFrame shape: {trends_data.shape}\n")
    else:
        print("Failed to fetch IOT data or no data was returned.\n")
        # Check what function did return
        print(f"The function returned: {iot_data}\n")
    
    print("="*50 + "\n")

    # Test 2: Related Queries [get_rq()]
    print("--- Testing Batch Related Queries ---\n")
    rq_keyword = ["Eileen Fisher", "Free People"]
    print(f"Fetching Related Queries data for: '{rq_keyword}'\n")
    rq_data = get_rq(rq_keyword)
    
    if rq_data:
        print("Successfully fetched RQ data. Results: \n")

        # Loop through dictionary structure
        for keyword, data in rq_data.items():
            print(f"--- Related Queries for '{keyword}' ---\n")

            top_df = data.get('top')
            if top_df is not None:
                print("--- Top ---\n")
                print(f"{top_df.to_string()}\n")
            else:
                print("No top queries found.\n")

            rising_df = data.get('rising')
            if rising_df is not None:
                print("--- Rising ---\n")
                print(f"{rising_df.to_string()}\n")
            else:
                print("No rising queries found.\n")
    else:
        print("Failed to fetch RQ data or no data was returned.\n")

    print("--- Test Complete ---\n")