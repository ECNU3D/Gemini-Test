import os
import asyncio
import aiohttp
import json
import time
import random
from dotenv import load_dotenv

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
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}
payloads = [
    {
        "model": model_name,
        "messages": [{"role": "user", "content": f"Tell me a short story #{i+1}"}],
        "max_tokens": 70,
        "temperature": 0.7 + i*0.05
    } for i in range(5) # Increase number of requests to potentially trigger rate limits
]

async def make_request_with_backoff(session, url, headers, payload, request_id):
    retries = 0
    backoff_time = INITIAL_BACKOFF_S
    while retries < MAX_RETRIES:
        print(f"[Request {request_id}, Attempt {retries+1}/{MAX_RETRIES}] Sending...")
        try:
            async with session.post(url, headers=headers, json=payload, timeout=60) as response:
                if response.status == 429:
                    print(f"[Request {request_id}, Attempt {retries+1}] Received 429 Rate Limit. Retrying in {backoff_time:.2f}s...")
                    # Check for retry-after header if available (optional, depends on API)
                    retry_after = response.headers.get("Retry-After")
                    wait = backoff_time
                    if retry_after:
                        try:
                            wait = max(backoff_time, float(retry_after)) # Use header if it's longer
                        except ValueError:
                            pass # Ignore invalid header value
                    await asyncio.sleep(wait)
                    retries += 1
                    backoff_time = min(MAX_BACKOFF_S, backoff_time * 2) + random.uniform(0, 1) # Exponential backoff with jitter
                    continue # Go to next retry iteration

                # If not 429, check for other client/server errors
                response.raise_for_status() # Raises HTTPError for 4xx/5xx responses other than 429 handled above

                # Success
                response_json = await response.json()
                print(f"[Request {request_id}, Attempt {retries+1}] Status: {response.status} - Success")
                # print(f"[Request {request_id}] Received Response: {json.dumps(response_json, indent=2)}") # Optional: print full response
                print(f"[Request {request_id}] Text: {response_json.get('choices', [{}])[0].get('message', {}).get('content', 'N/A').strip()}")
                return response_json

        except aiohttp.ClientError as e:
            print(f"[Request {request_id}, Attempt {retries+1}] Network/Client Error: {e}. Retrying in {backoff_time:.2f}s...")
        except asyncio.TimeoutError:
             print(f"[Request {request_id}, Attempt {retries+1}] Request timed out. Retrying in {backoff_time:.2f}s...")
        except Exception as e:
            # Catch other unexpected errors during request/response handling
            print(f"[Request {request_id}, Attempt {retries+1}] Unexpected error: {e}. Retrying in {backoff_time:.2f}s...")

        await asyncio.sleep(backoff_time)
        retries += 1
        backoff_time = min(MAX_BACKOFF_S, backoff_time * 2) + random.uniform(0, 1)

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
            make_request_with_backoff(session, chat_completions_url, headers, payload, i+1)
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