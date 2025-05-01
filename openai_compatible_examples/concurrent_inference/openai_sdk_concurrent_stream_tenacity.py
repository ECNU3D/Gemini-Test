import os
import asyncio
import time
import random
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from openai.types.chat import ChatCompletionChunk # For type hinting
from openai import AsyncStream # For type hinting
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, RetryError

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

# Configure the Async OpenAI client (disable built-in retries)
aclient = AsyncOpenAI(
    base_url=api_base_url,
    api_key=api_key,
    max_retries=0
)

all_messages = [
    [
        {"role": "user", "content": f"Write a short paragraph {i+1} about the ocean"}
    ] for i in range(5) # Increase requests
]

# --- Retry condition for OpenAI SDK ---
def should_retry_openai(exception):
    if isinstance(exception, RateLimitError):
        print(f"Retrying on RateLimitError: {exception}")
        return True
    if isinstance(exception, APITimeoutError):
        print(f"Retrying on APITimeoutError: {exception}")
        return True
    if isinstance(exception, APIError):
        if exception.status_code >= 500:
            print(f"Retrying on APIError status {exception.status_code}: {exception}")
            return True
    print(f"Not retrying on exception: {type(exception).__name__}: {exception}")
    return False
# ------------------------------------

@retry(
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=MIN_WAIT_S, max=MAX_WAIT_S),
    retry=retry_if_exception(should_retry_openai),
    reraise=True
)
async def initiate_openai_stream(messages, request_id):
    """Attempts to initiate the OpenAI stream, retrying on specific errors."""
    print(f"[Stream {request_id}] Attempting connection (attempt {initiate_openai_stream.retry.statistics['attempt_number']})...")
    stream = await aclient.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=100,
        temperature=0.7,
        stream=True,
        timeout=30.0
    )
    print(f"[Stream {request_id}] Stream initiated successfully.")
    return stream

async def process_openai_stream(stream: AsyncStream[ChatCompletionChunk], request_id):
    # (Same as before)
    print(f"[Stream {request_id}] Receiving data...")
    full_content = ""
    try:
        async for chunk in stream:
            content_piece = chunk.choices[0].delta.content or ""
            if content_piece:
                print(f"[Stream {request_id}] {content_piece}", end="", flush=True)
                full_content += content_piece
        print(f"\n[Stream {request_id}] Stream finished.")
    except APIError as e:
        print(f"\n[Stream {request_id}] OpenAI API Error during stream processing: {e}")
        if hasattr(e, 'status_code'):
            print(f"[Stream {request_id}] Status Code: {e.status_code}")
    except Exception as e:
        print(f"\n[Stream {request_id}] An unexpected error occurred during stream processing: {e}")
    finally:
        return full_content

async def run_openai_request_and_process(messages, request_id):
    """Wrapper to initiate SDK stream with retry and then process it."""
    stream = None
    try:
        stream = await initiate_openai_stream(messages, request_id)
        result = await process_openai_stream(stream, request_id)
        return result
    except RetryError as e:
        print(f"\n[Stream {request_id}] FAILED permanently after {MAX_ATTEMPTS} attempts (tenacity). Error: {e}")
        return None
    except Exception as e:
        print(f"\n[Stream {request_id}] FAILED with unexpected error: {type(e).__name__}: {e}")
        # Stream object might not exist or be closed already if error was in process_openai_stream
        return None

async def main():
    print(f"--- Sending {len(all_messages)} concurrent streaming requests using OpenAI SDK with tenacity ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print(f"Max Attempts: {MAX_ATTEMPTS}, Wait: Exp({MIN_WAIT_S}s-{MAX_WAIT_S}s)")
    print("---")

    start_time = time.time()
    semaphore = asyncio.Semaphore(3) # Limit concurrency

    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro

    tasks = [
        run_with_semaphore(run_openai_request_and_process(messages, i+1))
        for i, messages in enumerate(all_messages)
    ]
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    successful_results = [r for r in results if r is not None]
    print(f"\n--- All concurrent streams with tenacity finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Successful streams: {len(successful_results)}/{len(all_messages)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 