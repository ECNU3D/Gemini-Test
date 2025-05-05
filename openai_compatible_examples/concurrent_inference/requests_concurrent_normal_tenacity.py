import os
import asyncio
import aiohttp
import json
import time
import random
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, RetryError
from utils.auth_helpers import get_api_key_async # Use async version

# --- Tenacity Retry Settings ---
MAX_ATTEMPTS = 5
MIN_WAIT_S = 1
MAX_WAIT_S = 16
# ---------------------------

# Load environment variables
load_dotenv()
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
        "messages": [{"role": "user", "content": f"Generate a creative title {i+1}"}],
        "max_tokens": 30,
        "temperature": 0.8 + i*0.05
    } for i in range(5) # Increase requests
]

# --- Define which exceptions should trigger a retry ---
def should_retry_aiohttp(exception):
    """Return True if the exception is a retryable HTTP error."""
    if isinstance(exception, asyncio.TimeoutError):
        print(f"Retrying on TimeoutError: {exception}")
        return True
    if isinstance(exception, aiohttp.ClientResponseError):
        # Retry on 429 (Rate Limit) and 5xx server errors
        if exception.status == 429 or exception.status >= 500:
            print(f"Retrying on HTTP {exception.status}: {exception}")
            return True
    if isinstance(exception, aiohttp.ClientConnectionError):
        # Retry on connection errors
        print(f"Retrying on ClientConnectionError: {exception}")
        return True
    print(f"Not retrying on exception: {type(exception).__name__}: {exception}")
    return False
# -----------------------------------------------------

@retry(
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=MIN_WAIT_S, max=MAX_WAIT_S),
    retry=retry_if_exception(should_retry_aiohttp),
    reraise=True # Reraise the exception if all retries fail
)
async def send_request_with_tenacity(session, url, payload, request_id):
    # Fetch the latest API key *before* the first attempt by tenacity
    current_api_key = await get_api_key_async()
    headers = {**base_headers, "Authorization": f"Bearer {current_api_key}"}

    print(f"[Request {request_id}] Sending (attempt {send_request_with_tenacity.retry.statistics['attempt_number']})...")
    async with session.post(url, headers=headers, json=payload, timeout=30) as response:
        # Raise specific errors for tenacity to catch and potentially retry
        if response.status == 429 or response.status >= 500:
            print(f"[Request {request_id}] Status: {response.status} - Failed")
            return None
        response.raise_for_status() # Let tenacity catch ClientResponseError if status is bad
        response_json = await response.json()
        print(f"[Request {request_id}] Status: {response.status} - Success")
        print(f"[Request {request_id}] Text: {response_json.get('choices', [{}])[0].get('message', {}).get('content', 'N/A').strip()}")
        return response_json

async def main():
    print(f"--- Sending {len(payloads)} concurrent normal requests using aiohttp with tenacity backoff ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print(f"Max Attempts: {MAX_ATTEMPTS}, Wait: Exp({MIN_WAIT_S}s-{MAX_WAIT_S}s)")
    print("---")

    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, payload in enumerate(payloads):
            # Wrap the call in a separate task to handle potential final exceptions
            async def safe_request_wrapper(p, req_id):
                try:
                    return await send_request_with_tenacity(session, chat_completions_url, p, req_id)
                except Exception as e:
                    print(f"[Request {req_id}] FAILED permanently after all retries: {type(e).__name__}: {e}")
                    return None # Indicate failure
            tasks.append(safe_request_wrapper(payload, i+1))

        results = await asyncio.gather(*tasks)

    end_time = time.time()
    successful_results = [r for r in results if r is not None]
    print("\n--- All concurrent requests with tenacity backoff finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Successful requests: {len(successful_results)}/{len(payloads)}")
    # raise error if there are any failed requests
    if len(successful_results) != len(payloads):
        raise Exception("Failed to complete all requests.")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 