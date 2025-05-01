import os
import asyncio
import time
import random
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

# --- Tenacity Retry Settings ---
MAX_ATTEMPTS = 5
MIN_WAIT_S = 1
MAX_WAIT_S = 16
# ---------------------------

# Load environment variables
load_dotenv()
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
model_name = os.getenv("MODEL_NAME", "default-model")

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

# Configure the Async OpenAI client
# Disable SDK's built-in retries to rely solely on tenacity
aclient = AsyncOpenAI(
    base_url=api_base_url,
    api_key=api_key,
    max_retries=0
)

all_messages = [
    [
        {"role": "user", "content": f"Summarize concept {i+1}: Machine Learning"}
    ] for i in range(5) # Increase requests
]

# --- Define which exceptions should trigger a retry ---
def should_retry_openai(exception):
    """Return True if the exception is a retryable OpenAI API error."""
    if isinstance(exception, RateLimitError): # Specifically handles 429
        print(f"Retrying on RateLimitError: {exception}")
        return True
    if isinstance(exception, APITimeoutError):
        print(f"Retrying on APITimeoutError: {exception}")
        return True
    if isinstance(exception, APIError):
        # Retry on 5xx server errors
        if exception.status_code >= 500:
            print(f"Retrying on APIError status {exception.status_code}: {exception}")
            return True
    print(f"Not retrying on exception: {type(exception).__name__}: {exception}")
    return False
# -----------------------------------------------------

@retry(
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=MIN_WAIT_S, max=MAX_WAIT_S),
    retry=retry_if_exception(should_retry_openai),
    reraise=True # Reraise the exception if all retries fail
)
async def make_openai_request_with_tenacity(messages, request_id):
    print(f"[Request {request_id}] Sending (attempt {make_openai_request_with_tenacity.retry.statistics['attempt_number']})...")
    # No try/except needed here for tenacity-handled retries
    response = await aclient.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=100,
        temperature=0.7,
        stream=False,
        timeout=30.0
    )
    print(f"[Request {request_id}] Success")
    print(f"[Request {request_id}] Text: {response.choices[0].message.content.strip()}")
    return response


async def main():
    print(f"--- Sending {len(all_messages)} concurrent normal requests using OpenAI SDK with tenacity backoff ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print(f"Max Attempts: {MAX_ATTEMPTS}, Wait: Exp({MIN_WAIT_S}s-{MAX_WAIT_S}s)")
    print("---")

    start_time = time.time()
    semaphore = asyncio.Semaphore(3) # Limit concurrency

    async def run_with_semaphore(messages, req_id):
        async with semaphore:
            try:
                return await make_openai_request_with_tenacity(messages, req_id)
            except Exception as e:
                # Catch the exception if tenacity finally gives up
                print(f"[Request {req_id}] FAILED permanently after all retries: {type(e).__name__}: {e}")
                return None # Indicate failure

    tasks = [
        run_with_semaphore(messages, i+1)
        for i, messages in enumerate(all_messages)
    ]
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    successful_results = [r for r in results if r is not None]
    print("\n--- All concurrent requests with tenacity backoff finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Successful requests: {len(successful_results)}/{len(all_messages)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 