"""
Example of using an OpenAI-compatible Embeddings endpoint using the
official 'openai' Python SDK, specifically for batch processing.

Assumes the endpoint supports an embeddings route similar to OpenAI.
See: https://platform.openai.com/docs/api-reference/embeddings/create
"""

import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
# Embedding model name might be different from chat models
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002") # Example default

# --- Initialize OpenAI Client ---
# Point the client to the custom endpoint
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)

# --- API Request ---
# Input for batch processing will be a list of strings
input_text = [
    "This is the first sentence in the batch.",
    "Here is another sentence to embed in the batch.",
    "The third piece of text for batch embedding.",
    "Yet another item for the batch.",
    "Embedding multiple texts at once is efficient.",
    "This is sentence number six.",
    "Sentence seven checking in.",
    "The eighth entry in this batch example.",
    "Number nine, almost there.",
    "Finally, the tenth sentence for this batch."
]
# input_text = "A single input string." # Kept for reference, but batch uses list

def main():
    print("--- Sending BATCH request to embeddings endpoint ---")
    print(f"Model: {EMBEDDING_MODEL_NAME}")
    print(f"Input: {len(input_text)} items")
    # print(f"Input: {input_text}") # Commented out for brevity with many items
    print("-" * 30)

    try:
        start_time = time.monotonic() # Record start time
        response = client.embeddings.create(
            model=EMBEDDING_MODEL_NAME,
            input=input_text,
            # encoding_format="float", # Optional: "float" or "base64"
            # dimensions=1024        # Optional: If the model/endpoint supports it
        )
        end_time = time.monotonic() # Record end time
        processing_time = end_time - start_time

        print("--- Full API Response ---")
        # Use model_dump_json for cleaner output of Pydantic models
        print(response.model_dump_json(indent=2))
        print("-" * 30)

        # --- Response Handling ---
        if response.data and isinstance(response.data, list):
            print(f"Successfully received {len(response.data)} embedding(s) for the batch.")
            print(f"API call and initial processing took: {processing_time:.2f} seconds") # Print processing time

            for i, embedding_data in enumerate(response.data):
                # embedding_data is an Embedding object
                if embedding_data.embedding and isinstance(embedding_data.embedding, list):
                    embedding_vector = embedding_data.embedding
                    print(f"\n--- Embedding {i+1} (Batch Item) ---")
                    print(f"Original Text (first 30 chars): {input_text[i][:30]}...")
                    print(f"Object Type: {embedding_data.object}")
                    print(f"Index: {embedding_data.index}")
                    print(f"Dimensions: {len(embedding_vector)}")
                    # Print only the first few dimensions for brevity
                    print(f"Vector (first 5 dims): {embedding_vector[:5]}...")
                else:
                    print(f"Warning: Embedding data for batch item {i+1} seems malformed.")
                    print(embedding_data)

            # Also print usage info if available
            if response.usage:
                print("\n--- Usage Information ---")
                print(f"Prompt Tokens: {response.usage.prompt_tokens}")
                print(f"Total Tokens: {response.usage.total_tokens}")

        else:
            print("Response did not contain the expected 'data' list for the batch.")

    except (APIError, RateLimitError, APITimeoutError) as e:
        print(f"An API error occurred: {e}")
        if hasattr(e, 'status_code'):
            print(f"Status Code: {e.status_code}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"Response Body: {e.response.text}")
            except Exception:
                 print("Could not print response body.")
        elif hasattr(e, 'message'):
            print(f"Error Message: {e.message}")
        raise

    except KeyError as e:
        print(f"Error accessing expected key in API response: {e}")
        print("Response structure might be different than expected.")
        print(response.model_dump_json(indent=2) if 'response' in locals() else "No response object")
        raise

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print(f"Type: {type(e)}")
        raise

    print("-" * 30)
    print("Batch embeddings example complete.")

if __name__ == "__main__":
    main() 