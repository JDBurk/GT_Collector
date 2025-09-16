# arxiv_summarizer.py
# This module provides a function to summarize articles using Gemini API

from google import genai
from google.genai import types, errors

def summarize_text(client: genai.Client, text_to_summarize: str, model: str = "gemini-2.5-flash") -> str:
    """
    Uses the Gemini API to summarize a given text.

    Args:
        client (genai.Client): The Gemini API client.
        text_to_summarize (str): The text to be summarized
        model (str): The model to use for summarization.

    Returns:
        str: the concise summary created by the model
    """

    try:
        # Define the generation configuration for the summaries
        config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.8,
        )

        # Create a specific, instructive prompt for the model
        prompt = f"""
        Summarize the following research paper abstract in one or two concise sentences.
        Focus on the core contributions and the main outcomes of the article.

        Abstract:
        ---
        {text_to_summarize}
        ---
        """

        # Call the API
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
    
        return response.text.strip()
    
    except errors.APIError as e:
        print(f"An API error occurred during summarization: {e}")
        return "Error: Could not generate summary due to an API error."
    except Exception as e:
        # Basic error handling for other exceptions
        print(f"An unexpected error occurred during summarization: {e}")
        return "Error: Could not generate summary."

# This block is used to test the script when running directly
if __name__ == "__main__":
    # An example abstract from "Attention Is All You Need"
    example_abstract = """
    The dominant sequence transduction models are based on complex recurrent or
    convolutional neural networks, including an encoder and a decoder. The best
    performing models also connect the encoder and decoder through an attention
    mechanism. We propose a new simple network architecture, the Transformer,
    based solely on attention mechanisms, dispensing with recurrence and convolutions
    entirely. Experiments on two machine translation tasks show these models to

    be superior in quality while being more parallelizable and requiring significantly
    less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-
    to-German translation task, improving over the existing best results, including
    ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation
    task, our model establishes a new single-model state-of-the-art BLEU score of
    41.8 after training for 3.5 days on eight GPUs, a small fraction of the training
    costs of the best models from the literature. We show that the Transformer
    generalizes well to other tasks by applying it successfully to English constituency
    parsing both with large and limited training data.
    """
    print("--- Testing the Summarizer ---")
    print("\nOriginal Abstract:")
    print(example_abstract.strip())

    print("\n--- Generating Summary ---")
    # Initialize the client for testing
    test_client = genai.Client()
    gemini_summary = summarize_text(test_client, example_abstract)
    
    print("\nGemini Summary:")
    print(gemini_summary)
    print("\n--- Test Complete ---")