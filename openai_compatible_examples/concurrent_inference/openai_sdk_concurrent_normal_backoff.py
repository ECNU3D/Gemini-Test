import os
import asyncio
import time
import random
from openai import AsyncOpenAI, APIError, RateLimitError # Import RateLimitError
from dotenv import load_dotenv

# --- Retry Settings ---
MAX_RETRIES = 5
INITIAL_BACKOFF_S = 1
MAX_BACKOFF_S = 16
# --------------------

# Load environment variables
load_dotenv()
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
model_name = os.getenv("MODEL_NAME", "default-model")

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

# Configure the Async OpenAI client
# We can configure retries directly in the client, but we'll also add explicit loop for demonstration
aclient = AsyncOpenAI(
    base_url=api_base_url,
    api_key=api_key,
    max_retries=0 # Disable built-in retries to use our custom loop
)

all_messages = [
    [
        {"role": "user", "content": f"Explain concept {i+1} simply: Quantum Superposition"}
    ] for i in range(5) # Increase requests
]

async def make_openai_request_with_backoff(messages, request_id):
    retries = 0
    backoff_time = INITIAL_BACKOFF_S
    while retries < MAX_RETRIES:
        print(f"[Request {request_id}, Attempt {retries+1}/{MAX_RETRIES}] Sending...")
        try:
            response = await aclient.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=100,
                temperature=0.7,
                stream=False,
                timeout=60.0
            )
            print(f"[Request {request_id}, Attempt {retries+1}] Success")
            print(f"[Request {request_id}] Text: {response.choices[0].message.content.strip()}")
            return response
        except RateLimitError as e:
            print(f"[Request {request_id}, Attempt {retries+1}] Received RateLimitError (429). Retrying in {backoff_time:.2f}s...")
            # OpenAI SDK's RateLimitError might contain retry guidance, but it's not guaranteed
            # for all compatible APIs. We stick to exponential backoff here.
            # wait_time = e.response.headers.get("retry-after") # Example if header was accessible
        except APIError as e:
            # Handle other API errors (e.g., 5xx server errors)
            print(f"[Request {request_id}, Attempt {retries+1}] OpenAI API Error (Status: {e.status_code}): {e}. Retrying in {backoff_time:.2f}s...")
        except asyncio.TimeoutError:
             print(f"[Request {request_id}, Attempt {retries+1}] Request timed out. Retrying in {backoff_time:.2f}s...")
        except Exception as e:
            # Catch other unexpected errors
            print(f"[Request {request_id}, Attempt {retries+1}] Unexpected error: {e}. Retrying in {backoff_time:.2f}s...")

        # Wait and increase backoff time
        await asyncio.sleep(backoff_time)
        retries += 1
        backoff_time = min(MAX_BACKOFF_S, backoff_time * 2) + random.uniform(0, 1)

    print(f"[Request {request_id}] Failed after {MAX_RETRIES} retries.")
    return None

async def main():
    print(f"--- Sending {len(all_messages)} concurrent normal requests using OpenAI SDK with backoff ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print(f"Max Retries: {MAX_RETRIES}, Initial Backoff: {INITIAL_BACKOFF_S}s")
    print("---")

    start_time = time.time()
    semaphore = asyncio.Semaphore(3) # Limit concurrency

    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro

    tasks = [
        run_with_semaphore(make_openai_request_with_backoff(messages, i+1))
        for i, messages in enumerate(all_messages)
    ]
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    successful_results = [r for r in results if r is not None]
    print("\n--- All concurrent requests with backoff finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Successful requests: {len(successful_results)}/{len(all_messages)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 