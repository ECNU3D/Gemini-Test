"""
Example of using an OpenAI-compatible Embeddings endpoint using the
'requests' library.

Assumes the endpoint supports a POST request to /embeddings similar to OpenAI.
See: https://platform.openai.com/docs/api-reference/embeddings/create
"""

import os
import json
import requests
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
# Embedding model name might be different from chat models
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002") # Example default

EMBEDDINGS_URL = f"{API_BASE_URL}/embeddings"

def main():
    # --- API Request ---
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    # Input can be a string or a list of strings
    input_text = [
        "The quick brown fox jumps over the lazy dog.",
        "An example sentence for embedding."
    ]
    # input_text = "A single sentence to embed."

    payload = {
        "model": EMBEDDING_MODEL_NAME, # Model name is often required
        "input": input_text,
        # "encoding_format": "float", # Optional: e.g., "float" or "base64"
        # "dimensions": 1024,       # Optional: Request specific embedding dimensions if supported
    }

    # Remove None values from payload
    payload = {k: v for k, v in payload.items() if v is not None}

    print(f"--- Sending request to: {EMBEDDINGS_URL} ---")
    print(f"Payload:\n{json.dumps(payload, indent=2)}")
    print("-" * 30)

    try:
        response = requests.post(EMBEDDINGS_URL, headers=headers, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()
        print(f"--- Full API Response ---")
        print(json.dumps(response_data, indent=2))
        print("-" * 30)

        # --- Response Handling ---
        if response_data.get("data") and isinstance(response_data["data"], list):
            print(f"Successfully received {len(response_data['data'])} embedding(s).")

            for i, embedding_data in enumerate(response_data["data"]):
                if embedding_data.get("embedding") and isinstance(embedding_data["embedding"], list):
                    embedding_vector = embedding_data["embedding"]
                    print(f"\n--- Embedding {i+1} ---")
                    print(f"Object Type: {embedding_data.get('object')}")
                    print(f"Index: {embedding_data.get('index')}")
                    print(f"Dimensions: {len(embedding_vector)}")
                    # Print only the first few dimensions for brevity
                    print(f"Vector (first 5 dims): {embedding_vector[:5]}...")
                else:
                    print(f"Warning: Embedding data for item {i+1} seems malformed.")
                    print(embedding_data)

            # Also print usage info if available
            if response_data.get("usage"):
                print("\n--- Usage Information ---")
                print(json.dumps(response_data["usage"], indent=2))

        else:
            print("Response did not contain the expected 'data' list.")

    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")
        if e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            try:
                print(f"Response Body: {e.response.text}")
            except Exception:
                print("Could not print response body.")
        raise

    except KeyError as e:
        print(f"Error accessing expected key in API response: {e}")
        print("Response structure might be different than expected.")
        print(json.dumps(response_data if 'response_data' in locals() else {}, indent=2))
        raise

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

    print("-" * 30)
    print("Embeddings example complete.")

if __name__ == "__main__":
    main() 