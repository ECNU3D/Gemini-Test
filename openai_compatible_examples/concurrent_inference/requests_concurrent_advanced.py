import os
import asyncio
import time
import sys
import random
import requests
import json
from dotenv import load_dotenv

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key_async # Use async version

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
# api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Key fetched in send_openai_request
model_name = os.getenv("MODEL_NAME", "default-model")

REQUEST_TIMEOUT = 60  # Timeout in seconds (1 minute)

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

# Define multiple message sets for concurrent requests
all_messages = [
    [
        {"role": "user", "content": "Explain concept simply: Quantum Entanglement"}
    ],
    [
        {"role": "user", "content": "Explain concept simply: Blockchain"}
    ],
    [
        {"role": "user", "content": "Explain concept simply: General Relativity"}
    ]
]

def make_request_sync(url, headers, payload, timeout):
    """Synchronous function to make the HTTP request."""
    return requests.post(url, headers=headers, json=payload, timeout=timeout)

async def send_openai_request(messages, request_id, semaphore):
    task_start_time = time.time()
    print(f"[Request {request_id}] Waiting for semaphore...")
    async with semaphore:
        print(f"[Request {request_id}] Acquired semaphore, starting...")
        try:
            current_api_key = await get_api_key_async()
            if not current_api_key:
                print(f"[Request {request_id}] Failed to get API key.")
                return None

            headers = {
                "Authorization": f"Bearer {current_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model_name,
                "messages": messages,
                "max_tokens": 100,
                "temperature": 0.7,
                "stream": False
            }
            request_url = f"{api_base_url.rstrip('/')}/chat/completions" # Ensure correct endpoint construction

            # Use asyncio.to_thread to run the blocking requests.post call
            # and asyncio.wait_for for timeout on the async operation
            response = await asyncio.wait_for(
                asyncio.to_thread(make_request_sync, request_url, headers, payload, REQUEST_TIMEOUT),
                timeout=REQUEST_TIMEOUT + 5 # Add a small buffer for the to_thread overhead
            )

            response.raise_for_status()  # Raise an HTTPError for bad responses (4XX or 5XX)
            response_json = response.json()

            print(f"[Request {request_id}] Received Response:")
            # Adjust based on actual response structure if different from OpenAI SDK
            if response_json.get("choices") and response_json["choices"][0].get("message"):
                print(f"[Request {request_id}] {response_json['choices'][0]['message']['content'].strip()}")
            else:
                print(f"[Request {request_id}] Unexpected response structure: {response_json}")
            return response_json

        except asyncio.TimeoutError:
            # This now catches timeouts from asyncio.wait_for
            print(f"[Request {request_id}] Timed out after {REQUEST_TIMEOUT} seconds (overall task).")
        except requests.exceptions.Timeout:
            # This catches timeouts specifically from the requests library
            print(f"[Request {request_id}] Request timed out after {REQUEST_TIMEOUT} seconds (requests lib).")
        except requests.exceptions.HTTPError as e:
            print(f"[Request {request_id}] HTTP Error: {e.response.status_code} - {e.response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[Request {request_id}] Requests Library Error: {e}")
        except Exception as e:
            print(f"[Request {request_id}] An unexpected error occurred: {e}")
        return None

async def main():
    TOTAL_REQUESTS_TO_SEND = 10  # M: Total number of requests to send
    CONCURRENT_REQUESTS_LIMIT = 3 # N: Max number of concurrent requests

    print(f"--- Sending {TOTAL_REQUESTS_TO_SEND} requests with a concurrency limit of {CONCURRENT_REQUESTS_LIMIT} using requests lib ---")
    print(f"--- (Normal non-streaming requests) ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print("---")

    start_time = time.time()
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS_LIMIT)

    tasks = []
    for i in range(TOTAL_REQUESTS_TO_SEND):
        messages_set = all_messages[i % len(all_messages)]
        tasks.append(send_openai_request(messages_set, i + 1, semaphore))

    results = await asyncio.gather(*tasks)

    end_time = time.time()
    print("--- All requests finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    successful_results = [res for res in results if res is not None]
    print(f"Successfully completed {len(successful_results)} out of {TOTAL_REQUESTS_TO_SEND} requests.")
    if len(successful_results) != TOTAL_REQUESTS_TO_SEND:
        raise Exception(f"Failed to complete all {TOTAL_REQUESTS_TO_SEND} requests. Only {len(successful_results)} succeeded.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 