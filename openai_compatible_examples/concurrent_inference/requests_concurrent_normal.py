import os
import asyncio
import aiohttp
import json
import time
import sys
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
api_base = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Default to a dummy key if not set
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

# Define the endpoint URL
chat_completions_url = f"{api_base.rstrip('/')}/chat/completions"

# Define headers
base_headers = {
    "Content-Type": "application/json",
}

# Define multiple payloads for concurrent requests
payloads = [
    {
        "model": model_name,
        "messages": [{"role": "user", "content": f"Tell me joke #{i+1}"}],
        "max_tokens": 50,
        "temperature": 0.7 + i*0.1 # Vary temperature slightly
    } for i in range(3) # Create 3 concurrent requests
]

async def send_request(session, url, payload, request_id):
    task_start_time = time.time()
    print(f"[Request {request_id}] Starting...")
    try:
        # Fetch the latest API key asynchronously
        current_api_key = await get_api_key_async()
        headers = {**base_headers, "Authorization": f"Bearer {current_api_key}"}

        # Get proxy from environment variables
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")

        # Determine which proxy to use based on the URL scheme
        proxy_to_use = None
        if url.startswith("https://") and https_proxy:
            proxy_to_use = https_proxy
        elif url.startswith("http://") and http_proxy:
            proxy_to_use = http_proxy

        # print(f"[Request {request_id}] Using API Key: {current_api_key}") # Removed for similarity
        # print out all detailed request information for debug
        # print(f"[Request {request_id}] URL: {url}") # Removed for similarity
        # print(f"[Request {request_id}] Headers: {headers}") # Removed for similarity
        # print(f"[Request {request_id}] Payload: {payload}") # Removed for similarity
        # if proxy_to_use:
        #     print(f"[Request {request_id}] Using Proxy: {proxy_to_use}") # Removed for similarity

        async with session.post(url, headers=headers, json=payload, timeout=30, proxy=proxy_to_use) as response:
            response_data = await response.json()
            response.raise_for_status() # Raise an exception for bad status codes
            # print(f"[Request {request_id}] Status: {response.status}") # Removed for similarity
            # print(f"[Request {request_id}] Received Response: {json.dumps(response_data, indent=2)}") # Changed format
            print(f"[Request {request_id}] Received Response:")
            if response_data.get("choices") and response_data["choices"][0].get("message"):
                print(f"[Request {request_id}] {response_data['choices'][0]['message'].get('content', '').strip()}")
            else:
                print(f"[Request {request_id}] Response structure unexpected: {json.dumps(response_data)}")
            return response_data
    except aiohttp.ClientResponseError as e: # More specific error for HTTP status
        print(f"[Request {request_id}] HTTP Error: Status {e.status} - {e.message}")
        # Optionally log the response body if available
        try:
            error_body = await response.text() # Use response captured before error or re-read if needed and possible
            print(f"[Request {request_id}] Error Body: {error_body[:500]}") # Log first 500 chars
        except Exception:
            pass # Ignore if cannot read body
        return None
    except Exception as e:
        # print(f"[Request {request_id}] Error Type: {type(e)}") # Simplified error logging
        # print(f"[Request {request_id}] Error Repr: {repr(e)}") # Simplified error logging
        print(f"[Request {request_id}] Error: {e}")
        return None

async def main():
    # Updated print statement
    print(f"--- Sending {len(payloads)} concurrent normal (non-streaming) requests using aiohttp ---")
    # print(f"Target URL: {chat_completions_url}") # Changed to Base URL
    print(f"Base URL: {api_base}") # Use api_base which is already defined
    print(f"Model: {model_name}")
    print("---")

    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [
            send_request(session, chat_completions_url, payload, i+1)
            for i, payload in enumerate(payloads)
        ]
        results = await asyncio.gather(*tasks) # Run tasks concurrently

    end_time = time.time()
    print("--- All concurrent requests finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    # Add count of successful requests
    successful_results = [res for res in results if res is not None]
    print(f"Successfully completed {len(successful_results)} requests.")
    # You can process 'results' list here if needed
    # raise error if there are any failed requests
    if len(successful_results) != len(payloads):
        raise Exception("Failed to complete all requests.")


if __name__ == "__main__":
    # For Windows compatibility with asyncio in some environments
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 