import os
import asyncio
import aiohttp
import json
import time
import random
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, RetryError

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
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
    "Accept": "text/event-stream"
}
payloads = [
    {
        "model": model_name,
        "messages": [{"role": "user", "content": f"Write a haiku #{i+1}"}],
        "max_tokens": 40,
        "temperature": 0.7 + i*0.05,
        "stream": True
    } for i in range(5) # Increase requests
]

# --- Retry condition for aiohttp ---
def should_retry_aiohttp(exception):
    if isinstance(exception, asyncio.TimeoutError):
        print(f"Retrying on TimeoutError: {exception}")
        return True
    if isinstance(exception, aiohttp.ClientResponseError):
        if exception.status == 429 or exception.status >= 500:
            print(f"Retrying on HTTP {exception.status}: {exception}")
            return True
    if isinstance(exception, aiohttp.ClientConnectionError):
        print(f"Retrying on ClientConnectionError: {exception}")
        return True
    # Don't retry other ClientResponseErrors (like 400 Bad Request)
    print(f"Not retrying on exception: {type(exception).__name__}: {exception}")
    return False
# ------------------------------------

@retry(
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=MIN_WAIT_S, max=MAX_WAIT_S),
    retry=retry_if_exception(should_retry_aiohttp),
    reraise=True
)
async def initiate_stream_request(session, url, headers, payload, request_id):
    """Attempts to initiate the stream request, retrying on specific errors."""
    print(f"[Stream {request_id}] Attempting connection (attempt {initiate_stream_request.retry.statistics['attempt_number']})...")
    response = await session.post(url, headers=headers, json=payload, timeout=30)
    # Raise errors for tenacity to catch (429, 5xx, connection errors)
    # Note: We release the connection manually in the outer loop if needed.
    response.raise_for_status()
    print(f"[Stream {request_id}] Connection successful (Status: {response.status})")
    return response

async def process_stream(response, request_id):
    # (Same as before)
    print(f"[Stream {request_id}] Receiving data...")
    full_content = ""
    try:
        async for line in response.content:
            line_str = line.decode('utf-8').strip()
            if line_str.startswith("data:"):
                data_content = line_str[len("data:"):].strip()
                if data_content == "[DONE]":
                    print(f"\n[Stream {request_id}] Stream finished [DONE].")
                    break
                try:
                    chunk = json.loads(data_content)
                    if chunk.get("choices") and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        content_piece = delta.get("content", "")
                        if content_piece:
                            print(content_piece, end="", flush=True)
                            full_content += content_piece
                except json.JSONDecodeError:
                    print(f"\n[Stream {request_id}] Warning: Received non-JSON data: {data_content}")
            elif line_str:
                print(f"\n[Stream {request_id}] Received non-SSE line: {line_str}")
    except Exception as e:
        # Errors during stream processing are not retried by tenacity here
        print(f"\n[Stream {request_id}] Error during stream processing: {e}")
    finally:
        # print(f"[Stream {request_id}] Final content length: {len(full_content)}")
        await response.release() # Ensure connection is released after processing
        return full_content

async def run_request_and_process(session, url, headers, payload, request_id):
    """Wrapper to initiate request with retry and then process the stream."""
    response = None
    try:
        # Initiate stream, retrying with tenacity if necessary
        response = await initiate_stream_request(session, url, headers, payload, request_id)
        # If initiation succeeded, process the stream
        result = await process_stream(response, request_id)
        return result
    except RetryError as e:
        # This catches the error if tenacity gives up after all attempts
        print(f"[Stream {request_id}] FAILED permanently after {MAX_ATTEMPTS} attempts (tenacity). Error: {e}")
        return None
    except Exception as e:
        # Catch other unexpected errors (e.g., issues in process_stream not covered by retry)
        print(f"[Stream {request_id}] FAILED with unexpected error: {type(e).__name__}: {e}")
        # Ensure response is released if it exists and wasn't released by process_stream
        if response is not None and not response.closed:
            await response.release()
        return None


async def main():
    print(f"--- Sending {len(payloads)} concurrent streaming requests using aiohttp with tenacity ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print(f"Max Attempts: {MAX_ATTEMPTS}, Wait: Exp({MIN_WAIT_S}s-{MAX_WAIT_S}s)")
    print("---")

    start_time = time.time()
    semaphore = asyncio.Semaphore(3) # Limit concurrency

    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro

    async with aiohttp.ClientSession() as session:
        tasks = [
            run_with_semaphore(run_request_and_process(session, chat_completions_url, headers, payload, i+1))
            for i, payload in enumerate(payloads)
        ]
        results = await asyncio.gather(*tasks)

    end_time = time.time()
    successful_results = [r for r in results if r is not None]
    print(f"\n--- All concurrent streams with tenacity finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Successful streams: {len(successful_results)}/{len(payloads)}")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 