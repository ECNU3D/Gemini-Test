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
api_base_url = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
# Embedding model name might be different from chat models
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-ada-002") # Example default
INPUT_TEXT_MULTIPLIER = int(os.getenv("INPUT_TEXT_MULTIPLIER", "1")) # Default to 1 (10 sentences)
EMBEDDING_SEND_MODE = os.getenv("EMBEDDING_SEND_MODE", "batch").lower() # "batch" or "individual"

# --- Initialize OpenAI Client ---
# Point the client to the custom endpoint
client = OpenAI(
    base_url=api_base_url,
    api_key=api_key,
)

# --- API Request ---
# Input for batch processing will be a list of strings
base_input_sentences = [
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
input_text = [sentence * INPUT_TEXT_MULTIPLIER for sentence in base_input_sentences]

# input_text = "A single input string." # Kept for reference, but batch uses list

def main():
    print(f"--- Sending BATCH request to embeddings endpoint (Mode: {EMBEDDING_SEND_MODE}) ---")
    print(f"Model: {EMBEDDING_MODEL_NAME}")
    print(f"Input: {len(input_text)} items")
    # print(f"Input: {input_text}") # Commented out for brevity with many items
    print("-" * 30)

    total_processing_time = 0
    all_responses_data = []
    total_prompt_tokens = 0
    total_tokens_used = 0

    try:
        if EMBEDDING_SEND_MODE == "batch":
            start_time = time.monotonic() # Record start time
            response = client.embeddings.create(
                model=EMBEDDING_MODEL_NAME,
                input=input_text,
                # encoding_format="float", # Optional: "float" or "base64"
                # dimensions=1024        # Optional: If the model/endpoint supports it
            )
            end_time = time.monotonic() # Record end time
            total_processing_time = end_time - start_time

            print("--- Full API Response (Batch) ---")
            print(response.model_dump_json(indent=2))
            print("-" * 30)

            if response.data and isinstance(response.data, list):
                all_responses_data = response.data
            if response.usage:
                total_prompt_tokens = response.usage.prompt_tokens
                total_tokens_used = response.usage.total_tokens

        elif EMBEDDING_SEND_MODE == "individual":
            print("--- Sending requests individually ---")
            cumulative_start_time = time.monotonic()
            for item_index, item_text in enumerate(input_text):
                print(f"Sending item {item_index + 1}/{len(input_text)}: '{item_text[:50]}...'")
                item_start_time = time.monotonic()
                response = client.embeddings.create(
                    model=EMBEDDING_MODEL_NAME,
                    input=[item_text], # API expects a list, even for one item
                    # encoding_format="float",
                    # dimensions=1024
                )
                item_end_time = time.monotonic()
                item_processing_time = item_end_time - item_start_time
                total_processing_time += item_processing_time
                print(f"Item {item_index + 1} processed in {item_processing_time:.2f}s")

                if response.data and isinstance(response.data, list) and len(response.data) > 0:
                    # Ensure the .index aligns with the overall batch, not just this single call
                    # The API for single item might still return index 0, so we overwrite it
                    response.data[0].index = item_index
                    all_responses_data.append(response.data[0])
                if response.usage:
                    total_prompt_tokens += response.usage.prompt_tokens
                    total_tokens_used += response.usage.total_tokens
            cumulative_end_time = time.monotonic()
            print(f"All individual requests took: {cumulative_end_time - cumulative_start_time:.2f}s (sum of API times: {total_processing_time:.2f}s)")
            print("-" * 30)

        else:
            print(f"Error: Unknown EMBEDDING_SEND_MODE: '{EMBEDDING_SEND_MODE}'")
            return

        # --- Response Handling (unified for both modes) ---
        if all_responses_data:
            print(f"Successfully received {len(all_responses_data)} embedding(s) in '{EMBEDDING_SEND_MODE}' mode.")
            if EMBEDDING_SEND_MODE == "batch": # Only print for batch, individual prints per item
                 print(f"API call and initial processing took: {total_processing_time:.2f} seconds")

            for i, embedding_data in enumerate(all_responses_data):
                if embedding_data.embedding and isinstance(embedding_data.embedding, list):
                    embedding_vector = embedding_data.embedding
                    # Determine original text based on index. For individual mode, embedding_data.index was set correctly.
                    # For batch mode, `i` and `embedding_data.index` should match.
                    original_text_display = input_text[embedding_data.index][:30] if embedding_data.index < len(input_text) else "N/A"

                    print(f"\n--- Embedding {embedding_data.index + 1} (Original Index) ---")
                    print(f"Original Text (first 30 chars): {original_text_display}...")
                    print(f"Object Type: {embedding_data.object}")
                    # print(f"Processed Index in this list: {i}") # For debugging if needed
                    print(f"Reported Index by API: {embedding_data.index}")
                    print(f"Dimensions: {len(embedding_vector)}")
                    print(f"Vector (first 5 dims): {embedding_vector[:5]}...")
                else:
                    print(f"Warning: Embedding data for item with original index {embedding_data.index if hasattr(embedding_data, 'index') else i} seems malformed.")
                    print(embedding_data)

            if total_prompt_tokens > 0 or total_tokens_used > 0:
                print("\n--- Aggregated Usage Information ---")
                print(f"Total Prompt Tokens: {total_prompt_tokens}")
                print(f"Total Tokens: {total_tokens_used}")
        else:
            print(f"Response did not contain the expected 'data' list in '{EMBEDDING_SEND_MODE}' mode.")

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