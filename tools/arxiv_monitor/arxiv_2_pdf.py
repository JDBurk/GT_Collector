# arxiv_2_pdf.py
import os
import re
import requests

def arxiv_2_pdf(pdf_url: str, title: str):
    """
    Downloads a PDF from a given URL and saves it with the specified title.

    Args:
        pdf_url (str): the URL of the PDF to download.
        title (str): the title of the paper, used for the filename.
    """

    try:
        # Sanitize the title to create a valid filename
        # Remove invalid characters and replace spaces with underscores
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title).replace(' ', '_')
        filename = f"{safe_title}.pdf"

        # Define the downloads directory and create it if it doesn't exist
        download_dir = os.path.join("downloads", "arxiv_dl")
        os.makedirs(download_dir, exist_ok=True)
        filepath = os.path.join(download_dir, filename)
        
        """ 
        ### To save directly to ~home downloads folder
        download_dir = os.path.join(os.path.expanduser("~"), "downloads", "arxiv_dl")

        ### Build relative path to root folder
        # Get the directory of the current script file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Navigate up to the project's root directory
        project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
        # Now, build the path from the project root
        download_dir = os.path.join(project_root, "downloads", "arxiv_dl")
        """

        print(f"Downloading {filename}...\n")

        # Make the request to the URL
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status() # This raises error for bad responses (4xx or 5xx)

        # Write the content to the file in chunks
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Successfully saved to {filepath}\n")
    
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
    except IOError as e:
        print(f"Error saving PDF: {e}")

# Test Block
if __name__ == "__main__":
    # test URL for a little known paper (Attention is All You Need)
    test_url = "https://arxiv.org/pdf/1706.03762.pdf"
    test_title = "Attention Is All You Need"
    print("--- Testing arxiv_2_pdf ---")
    arxiv_2_pdf(test_url, test_title)
    print("--- Test Complete ---")
        
