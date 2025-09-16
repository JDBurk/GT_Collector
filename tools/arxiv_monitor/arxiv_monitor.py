# arxiv_monitor.py

# Import functions from other modules
import argparse
import datetime
import os
from arxiv_tool import search_arxiv
from arxiv_summarizer import summarize_text
from arxiv_2_pdf import arxiv_2_pdf
from google import genai

def main():
    """
    Function to run the arXiv monitor agent via a CLI.
    """
    
    print("\n--- arXiv Monitor Agent ---\n")
    
    # Setup argument parser
    # Run CLI with terminal prompt below, query is always required (no default)
    # python tools/arxiv_monitor/arxiv_monitor.py -q "QUERY" -n NUMBER_PAPERS -s "SORT_BY" -o "OUTPUT_TYPE"
    parser = argparse.ArgumentParser(description="An AI-powered tool to search, summarize, and manage arXiv papers.")
    parser.add_argument("-q", "--query", type=str, required=True, help="Search query for arXiv papers.")
    parser.add_argument("-n", "--num_papers", type=int, default=3, help="Number of papers to retrieve (default is 3).")
    parser.add_argument("-s", "--sort_by", type=str, choices=["relevance", "updated", "submitted"], default="submitted", 
                        help="Sorting criterion (default is 'submitted')")
    parser.add_argument("-o", "--output", type=str, default=None, help="Optional filename to save the report.")

    args = parser.parse_args()

    # Use the arguments provided by the user
    query = args.query
    num_papers = args.num_papers
    sort_choice = args.sort_by
    output_filename = args.output

    # Define/ create output directory
    output_dir = os.path.join("downloads", "arxiv_dl")
    os.makedirs(output_dir, exist_ok=True)

    # If no output filename is given, create a default one:
    if not output_filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c for c in query if c.isalnum() or c in " _-").rstrip()
        output_filename = f"arxiv_report_{safe_query}_{timestamp}.txt"
    
    # Construct path to file
    output_filepath = os.path.join(output_dir, output_filename)

    # Confirm selections while beginning query        
    print(f"\nSearching for {num_papers} papers on '{query}', sorted by '{sort_choice}'...\n")
    print(f"Results will be saved to {output_filepath}\n")

    # Perform the search
    papers = search_arxiv(query, max_results = num_papers, sort_by = sort_choice)
    papers_list = list(papers)  # Search returns a generator, convert to list for easier handling

    # If no papers are found...
    if not papers_list:
        print("No papers found.")
        return # Exit the function

    print(f"Found {len(papers_list)} papers. Starting summarization...\n")

    # Initialize the Gemini client once
    client = genai.Client()

    # Open the file to write the report
    with open(output_filepath, 'a', encoding='utf-8') as report_file:
        # Write a header for this session
        report_file.write(f"--- arXiv Report: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')} ---\n\n")
        report_file.write(f"Search Query: '{query}' | # of Papers: {num_papers} | Sort: {sort_choice}\n")
        report_file.write("="*50 + "\n\n")

        for i, paper in enumerate(papers_list):
            # Build the output string
            output_block = (
                f"--- [ Paper {i+1}/{len(papers_list)} ] ---\n"
                f"Title: {paper.title}\n"
                f"Published: {paper.published}\n"
                f"Link: {paper.pdf_url}\n"
                #author_names = ", ".join(author.name for author in paper.authors)
                #f"Authors: {author_names}\n"
                "Generating summary...\n"
            )

            print(output_block)
            report_file.write(output_block)

            # Call summarization function by feeding abstract to Gemini
            gemini_summary = summarize_text(client, paper.summary) # Specify model by adding input value

            summary_block = f"Gemini Summary: {gemini_summary}\n\n"
            print(summary_block)
            report_file.write(summary_block)

            # Prompt user about PDF download
            download_choice = input("Download this paper as PDF? (y/n): ").strip().lower()
            print("\n")
            if download_choice == 'y':
                # If yes, call arxiv_2_pdf with the paper's details
                arxiv_2_pdf(paper.pdf_url, paper.title)
                report_file.write("[User chose to download this PDF.]\n\n")

    print(f"--- [ Process Complete ] ---\nReport saved to '{output_filepath}'\n\n")

if __name__ == "__main__":
    main()
        
    