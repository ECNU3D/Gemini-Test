"""
Example demonstrating interaction with an OpenAI-compatible Batch API endpoint
using the 'openai' Python SDK.

NOTE: This example assumes the target endpoint implements the OpenAI Batch API.
Functionality and availability may vary significantly between providers.
This script focuses on the workflow: uploading a batch file, creating a batch job,
and checking its status.

It requires a pre-formatted batch input file (JSONL).

See: https://platform.openai.com/docs/api-reference/batch
See: https://platform.openai.com/docs/guides/batch
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")

# --- !! IMPORTANT !! ---
# Path to your batch input file (JSONL format)
# Each line must be a valid JSON object representing a single API request.
# Example line for /v1/chat/completions:
# {"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello world!"}]}}
BATCH_INPUT_FILE_PATH = "./example_batch_input.jsonl" # NEEDS TO BE CREATED MANUALLY
BATCH_INPUT_FILENAME = Path(BATCH_INPUT_FILE_PATH).name

# Endpoint for batch requests (usually /v1/batches)
# The SDK uses client.batches.create(), client.batches.retrieve(), etc.

# --- Initialize OpenAI Client ---
# Point the client to the custom endpoint
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)

# --- Helper Function to Create Batch File (for demonstration) ---
def create_dummy_batch_file(filepath):
    print(f"--- Creating dummy batch input file: {filepath} ---")
    # Example content for chat completions
    # NOTE: Ensure the model name in 'body' matches a model available on your endpoint
    example_requests = [
        {"custom_id": "req_1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": os.getenv("MODEL_NAME", "default-model"), "messages": [{"role": "user", "content": "What is 2+2?"}], "max_tokens": 10}},
        {"custom_id": "req_2", "method": "POST", "url": "/v1/chat/completions", "body": {"model": os.getenv("MODEL_NAME", "default-model"), "messages": [{"role": "user", "content": "Translate 'hello' to French."}], "max_tokens": 10}},
        # Add more requests as needed
    ]
    try:
        with open(filepath, 'w') as f:
            for req in example_requests:
                f.write(json.dumps(req) + '\n')
        print(f"Dummy file '{filepath}' created successfully.")
        return True
    except Exception as e:
        print(f"Error creating dummy file: {e}")
        return False

# --- Main Batch API Interaction ---
def main():
    batch_file_id = None
    batch_job_id = None

    # 1. Create the dummy input file (replace with your actual file creation/check)
    if not Path(BATCH_INPUT_FILE_PATH).exists():
        if not create_dummy_batch_file(BATCH_INPUT_FILE_PATH):
            print("Cannot proceed without batch input file.")
            return
    else:
        print(f"Using existing batch input file: {BATCH_INPUT_FILE_PATH}")

    print("-" * 30)

    try:
        # 2. Upload the Batch File
        # The Batch API requires the file to be uploaded first to get a file ID.
        print(f"--- Uploading batch file: {BATCH_INPUT_FILENAME} ---")
        with open(BATCH_INPUT_FILE_PATH, "rb") as f:
            batch_file_object = client.files.create(
                file=f,
                purpose="batch"
            )
        batch_file_id = batch_file_object.id
        print(f"File uploaded successfully. File ID: {batch_file_id}")
        print(f"File Object:\\n{batch_file_object.model_dump_json(indent=2)}")
        print("-" * 30)

        # 3. Create the Batch Job
        print(f"--- Creating batch job using File ID: {batch_file_id} ---")
        batch_job = client.batches.create(
            input_file_id=batch_file_id,
            endpoint="/v1/chat/completions", # The API endpoint each line in the batch file targets
            completion_window="24h", # How long the batch job is allowed to run
            metadata={
                'description': 'Example batch job from SDK script'
            }
        )
        batch_job_id = batch_job.id
        print(f"Batch job created successfully. Batch ID: {batch_job_id}")
        print(f"Batch Object:\\n{batch_job.model_dump_json(indent=2)}")
        print("-" * 30)

        # 4. Poll for Batch Job Status
        print(f"--- Polling status for Batch ID: {batch_job_id} ---")
        while True:
            batch_job_status = client.batches.retrieve(batch_job_id)
            status = batch_job_status.status
            print(f"Current Status: {status} ({time.strftime('%Y-%m-%d %H:%M:%S')})")

            if status in ["completed", "failed", "cancelled", "expired"]:
                print(f"Batch job finished with status: {status}")
                print(f"Final Batch Object:\\n{batch_job_status.model_dump_json(indent=2)}")
                break # Exit the polling loop

            # Wait before polling again (e.g., 30 seconds)
            print("Waiting 30 seconds before next status check...")
            time.sleep(30)

        print("-" * 30)

        # 5. Retrieve Batch Results (if completed)
        if batch_job_status.status == "completed":
            output_file_id = batch_job_status.output_file_id
            error_file_id = batch_job_status.error_file_id

            if output_file_id:
                print(f"--- Retrieving results from Output File ID: {output_file_id} ---")
                # Get the content of the output file
                # Note: The actual content retrieval might depend on the endpoint's implementation
                # OpenAI SDK returns a FileContent object which needs further handling.
                try:
                    output_content_response = client.files.content(output_file_id)
                    # The response object itself might not directly contain the text/bytes.
                    # You often need to read from the response stream or access specific attributes.
                    # This part is highly dependent on the SDK version and how the stream is exposed.
                    # Example (conceptual - may need adjustment):
                    output_data = output_content_response.text # Or .read(), .content etc.
                    print("Output File Content (first 500 chars):")
                    print(output_data[:500])

                    # Save the results to a local file
                    output_filename = f"batch_output_{batch_job_id}.jsonl"
                    with open(output_filename, "w") as f_out:
                        f_out.write(output_data)
                    print(f"Full output saved to: {output_filename}")

                except Exception as e_content:
                    print(f"Error retrieving or reading output file content: {e_content}")
                    print("You might need to manually download the file using the ID.")
            else:
                print("No output file ID found for the completed batch job.")

            if error_file_id:
                 print(f"--- Errors reported in Error File ID: {error_file_id} --- (Content retrieval not shown)")
                 # Similar content retrieval logic applies here if needed.

        else:
            print(f"Batch job did not complete successfully (Status: {batch_job_status.status}). Cannot retrieve results.")

    except (APIError, RateLimitError, APITimeoutError) as e:
        print(f"An API error occurred during batch processing: {e}")
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

    except FileNotFoundError:
        print(f"Error: Batch input file not found at '{BATCH_INPUT_FILE_PATH}'")
        raise

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print(f"Type: {type(e)}")
        raise

    finally:
        # Optional: Clean up uploaded file and local dummy file
        # Be cautious with deleting files, especially the input/output if needed later.
        # if batch_file_id:
        #     try:
        #         print(f"--- Attempting to delete uploaded file: {batch_file_id} ---")
        #         client.files.delete(batch_file_id)
        #         print("Uploaded file deleted.")
        #     except Exception as e_del:
        #         print(f"Could not delete uploaded file {batch_file_id}: {e_del}")
        # if Path(BATCH_INPUT_FILE_PATH).exists() and BATCH_INPUT_FILENAME == "example_batch_input.jsonl":
        #      try:
        #          print(f"--- Deleting local dummy file: {BATCH_INPUT_FILE_PATH} ---")
        #          os.remove(BATCH_INPUT_FILE_PATH)
        #          print("Local dummy file deleted.")
        #      except Exception as e_del_local:
        #          print(f"Could not delete local file {BATCH_INPUT_FILE_PATH}: {e_del_local}")
        pass # Avoid automatic deletion by default

    print("-" * 30)
    print("Batch API example complete.")


if __name__ == "__main__":
    main() 