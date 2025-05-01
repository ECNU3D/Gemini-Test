import os
import asyncio
import time
import random
from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError
from openai.types.chat import ChatCompletionChunk # For type hinting
from openai import AsyncStream # For type hinting
from dotenv import load_dotenv
from utils.auth_helpers import get_api_key_async # Use async version

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

# Initialize client - Key will be updated before retries
aclient = AsyncOpenAI(
    base_url=api_base_url,
    api_key="dummy-key", # Placeholder
    max_retries=0       # Disable built-in retries
)

all_messages = [
    [
        {"role": "user", "content": f"Write a very short poem {i+1} about space travel"}
    ] for i in range(5) # Increase requests
]

async def process_openai_stream(stream, request_id):
    # (This function remains the same as the non-backoff version)
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
        # Add status code if available in the error during streaming
        if hasattr(e, 'status_code'):
            print(f"[Stream {request_id}] Status Code: {e.status_code}")
    except Exception as e:
        print(f"\n[Stream {request_id}] An unexpected error occurred during stream processing: {e}")
    finally:
        # print(f"[Stream {request_id}] Final content length: {len(full_content)}") # Less useful during concurrent prints
        return full_content

async def make_openai_streaming_request_with_backoff(messages, request_id):
    retries = 0
    backoff_time = INITIAL_BACKOFF_S
    while retries < MAX_RETRIES:
        print(f"[Stream {request_id}, Attempt {retries+1}/{MAX_RETRIES}] Sending request...")
        try:
            # Attempt to create the stream
            stream = await aclient.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=100,
                temperature=0.7,
                stream=True,
                timeout=60.0
            )
            print(f"[Stream {request_id}, Attempt {retries+1}] Stream initiated successfully.")
            # Process the stream
            result = await process_openai_stream(stream, request_id)
            return result # Success

        except RateLimitError as e:
            print(f"\n[Stream {request_id}, Attempt {retries+1}] Received RateLimitError (429). Retrying in {backoff_time:.2f}s...")
        except APIError as e:
            print(f"\n[Stream {request_id}, Attempt {retries+1}] OpenAI API Error (Status: {e.status_code}): {e}. Retrying in {backoff_time:.2f}s...")
        except asyncio.TimeoutError:
             print(f"\n[Stream {request_id}, Attempt {retries+1}] Request timed out. Retrying in {backoff_time:.2f}s...")
        except Exception as e:
            print(f"\n[Stream {request_id}, Attempt {retries+1}] Unexpected error creating stream: {e}. Retrying in {backoff_time:.2f}s...")

        # Wait and increase backoff time if an error occurred before/during stream creation
        await asyncio.sleep(backoff_time)
        retries += 1
        backoff_time = min(MAX_BACKOFF_S, backoff_time * 2) + random.uniform(0, 1)

    print(f"\n[Stream {request_id}] Failed after {MAX_RETRIES} retries.")
    return None

async def main():
    print(f"--- Sending {len(all_messages)} concurrent streaming requests using OpenAI SDK with backoff ---")
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
        run_with_semaphore(make_openai_streaming_request_with_backoff(messages, i+1))
        for i, messages in enumerate(all_messages)
    ]
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    successful_results = [r for r in results if r is not None]
    print(f"\n--- All concurrent streams with backoff finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Successful streams: {len(successful_results)}/{len(all_messages)}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 