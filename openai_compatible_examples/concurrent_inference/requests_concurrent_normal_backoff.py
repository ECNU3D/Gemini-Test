import os
import asyncio
import aiohttp
import json
import time
import random
from dotenv import load_dotenv
from utils.auth_helpers import get_api_key_async

# --- Retry Settings ---
MAX_RETRIES = 5
INITIAL_BACKOFF_S = 1
MAX_BACKOFF_S = 16
# --------------------

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
model_name = os.getenv("MODEL_NAME", "default-model")

if not api_base:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

chat_completions_url = f"{api_base.rstrip('/')}/chat/completions"
base_headers = {
    "Content-Type": "application/json",
}
payloads = [
    {
        "model": model_name,
        "messages": [{"role": "user", "content": f"Tell me a short story #{i+1}"}],
        "max_tokens": 70,
        "temperature": 0.7 + i*0.05
    } for i in range(5) # Increase number of requests to potentially trigger rate limits
]

async def send_request_with_retry(session, url, payload, request_id):
    task_start_time = time.time()
    print(f"[Request {request_id}] Starting (with retry)...Attempt 1")
    # Fetch initial key outside the loop
    current_api_key = await get_api_key_async()

    for attempt in range(MAX_RETRIES):
        wait_time = min(INITIAL_BACKOFF_S * (2 ** attempt), MAX_BACKOFF_S)
        # Add jitter: random small amount +/- up to 1 second
        jitter = random.uniform(-1, 1)
        actual_wait = max(0, wait_time + jitter)

        try:
            # Refresh key ONLY if it's not the first attempt
            # Assuming key *might* have expired during wait
            if attempt > 0:
                print(f"[Request {request_id}] Refreshing API key before attempt {attempt + 1}...")
                current_api_key = await get_api_key_async()

            headers = {**base_headers, "Authorization": f"Bearer {current_api_key}"}

            async with session.post(url, headers=headers, json=payload, timeout=60) as response:
                if response.status == 429:
                    print(f"[Request {request_id}, Attempt {attempt+1}] Received 429 Rate Limit. Retrying in {actual_wait:.2f}s...")
                    # Check for retry-after header if available (optional, depends on API)
                    retry_after = response.headers.get("Retry-After")
                    wait = actual_wait
                    if retry_after:
                        try:
                            wait = max(actual_wait, float(retry_after)) # Use header if it's longer
                        except ValueError:
                            pass # Ignore invalid header value
                    await asyncio.sleep(wait)
                    continue # Go to next retry iteration

                # If not 429, check for other client/server errors
                response.raise_for_status() # Raises HTTPError for 4xx/5xx responses other than 429 handled above

                # Success
                response_json = await response.json()
                print(f"[Request {request_id}, Attempt {attempt+1}] Status: {response.status} - Success")
                # print(f"[Request {request_id}] Received Response: {json.dumps(response_json, indent=2)}") # Optional: print full response
                print(f"[Request {request_id}] Text: {response_json.get('choices', [{}])[0].get('message', {}).get('content', 'N/A').strip()}")
                return response_json

        except aiohttp.ClientError as e:
            print(f"[Request {request_id}, Attempt {attempt+1}] Network/Client Error: {e}. Retrying in {actual_wait:.2f}s...")
        except asyncio.TimeoutError:
             print(f"[Request {request_id}, Attempt {attempt+1}] Request timed out. Retrying in {actual_wait:.2f}s...")
        except Exception as e:
            # Catch other unexpected errors during request/response handling
            print(f"[Request {request_id}, Attempt {attempt+1}] Unexpected error: {e}. Retrying in {actual_wait:.2f}s...")

        await asyncio.sleep(actual_wait)

    print(f"[Request {request_id}] Failed after {MAX_RETRIES} retries.")
    return None # Indicate failure


async def main():
    print(f"--- Sending {len(payloads)} concurrent normal requests using aiohttp with backoff ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print(f"Max Retries: {MAX_RETRIES}, Initial Backoff: {INITIAL_BACKOFF_S}s")
    print("---")

    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [
            send_request_with_retry(session, chat_completions_url, payload, i+1)
            for i, payload in enumerate(payloads)
        ]
        results = await asyncio.gather(*tasks) # Run tasks concurrently

    end_time = time.time()
    successful_results = [r for r in results if r is not None]
    print("\n--- All concurrent requests with backoff finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Successful requests: {len(successful_results)}/{len(payloads)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 