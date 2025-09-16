# arxiv_tool.py
# This module provides a function to fetch and parse arXiv papers.

#import libraries
import arxiv

# Map strings to Arxiv Enum for sort criteria
SORT_CRITERIA_MAP = {
    "relevance": arxiv.SortCriterion.Relevance,
    "updated": arxiv.SortCriterion.LastUpdatedDate, # last_updated_date
    "submitted": arxiv.SortCriterion.SubmittedDate  # submitted_date
}

def search_arxiv(query: str, max_results: int = 3, sort_by: str = "submitted"):
    """
    Searches the arXiv API for a given query and returns the results.

    Args:
        query (str): the search term to look for
        max_results (int): The maximum number of results to return
        sort_by (str): The sorting criterion, can only be "relevance", "last_updated_date", or "submitted_date"
    
    Returns:
        A generator of arxiv.Result objects
    """
    # create a client to search arXiv
    client = arxiv.Client()

    # look up sort criterion from the map and provide a safe default value
    sort_criterion = SORT_CRITERIA_MAP.get(sort_by.lower())
    if not sort_criterion:
        print(f"Warning: Invalid sort_by value '{sort_by}'. Defaulting to 'submitted'.")
        sort_criterion = arxiv.SortCriterion.Relevance

    # create a search object using the function parameters
    search = arxiv.Search(
        query = query,
        max_results = max_results,
        sort_by = sort_criterion
        # sort_order = arxiv.SortOrder.Descending
    )

    # perform the search using client.results() method
    results = client.results(search)

    # return the results generator to the caller
    return results

# This block is used to directly test the search_arxiv function
if __name__ == "__main__":
    print("\n--- Running a test search for 'Large Language Models' ---")
    
    # call function with a test query
    test_query = "Reinforcement Learning"
    llm_papers = search_arxiv(test_query, 5, sort_by="submitted")

    # convert generator (results) to a list to easily check count
    papers_list = list(llm_papers)
    print(f"Found {len(papers_list)} papers on '{test_query}'") # sorted by {sort_by}
    print("---\n")

    
    # Loop through the results and print details
    for result in papers_list:
        print(f"Title: {result.title}")
        print(f"Published: {result.published}")
        print(f"Link: {result.pdf_url}\n")
        # author_names = ", ".join(author.name for author in result.authors) # Lists paper's authors
        #print(f"Authors: {author_names}")