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
        "messages": [{"role": "user", "content": f"Write a long poem #{i+1}"}],
        "max_tokens": 120,
        "temperature": 0.6 + i*0.05,
        "stream": True
    } for i in range(5) # Increase requests
]

async def process_stream(response, request_id):
    # (This function remains the same as the non-backoff version)
    print(f"[Stream {request_id}] Receiving data...")
    full_content = ""
    try:
        async for line in response.content:
            line_str = line.decode('utf-8').strip()
            if line_str.startswith("data:"):
                data_content = line_str[len("data:"):].strip()
                if data_content == "[DONE]":
                    print(f"\n[Stream {request_id}] Stream finished.")
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
        print(f"\n[Stream {request_id}] Error processing stream: {e}")
    finally:
        print(f"[Stream {request_id}] Final content length: {len(full_content)}")
        return full_content

async def make_streaming_request_with_backoff(session, url, headers, payload, request_id):
    retries = 0
    backoff_time = INITIAL_BACKOFF_S
    while retries < MAX_RETRIES:
        print(f"[Stream {request_id}, Attempt {retries+1}/{MAX_RETRIES}] Sending request...")
        response = None # Ensure response is defined in this scope
        try:
            response = await session.post(url, headers=headers, json=payload, timeout=60)
            print(f"[Stream {request_id}, Attempt {retries+1}] Status: {response.status}")

            if response.status == 429:
                print(f"[Stream {request_id}, Attempt {retries+1}] Received 429 Rate Limit. Retrying in {backoff_time:.2f}s...")
                # Optionally check Retry-After header
                retry_after = response.headers.get("Retry-After")
                wait = backoff_time
                if retry_after:
                    try:
                        wait = max(backoff_time, float(retry_after))
                    except ValueError:
                        pass
                await response.release() # Crucial: Release connection before sleeping
                await asyncio.sleep(wait)
                retries += 1
                backoff_time = min(MAX_BACKOFF_S, backoff_time * 2) + random.uniform(0, 1)
                continue # Go to next retry

            # Check for other errors before attempting to stream
            response.raise_for_status() # Raise for other 4xx/5xx

            # If status is OK (200), process the stream
            if response.status == 200:
                result = await process_stream(response, request_id)
                return result # Success
            else:
                 # Should be caught by raise_for_status, but as fallback
                error_text = await response.text()
                print(f"[Stream {request_id}, Attempt {retries+1}] Unexpected Status {response.status}: {error_text}. Retrying...")

        except aiohttp.ClientError as e:
            print(f"[Stream {request_id}, Attempt {retries+1}] Network/Client Error: {e}. Retrying in {backoff_time:.2f}s...")
        except asyncio.TimeoutError:
            print(f"[Stream {request_id}, Attempt {retries+1}] Request timed out. Retrying in {backoff_time:.2f}s...")
        except Exception as e:
            print(f"[Stream {request_id}, Attempt {retries+1}] Unexpected error: {e}. Retrying in {backoff_time:.2f}s...")
        finally:
            # Ensure the response connection is released if it exists and wasn't released earlier
            if response is not None and not response.closed:
                response.release()

        # If we reached here, an error occurred and we need to backoff
        await asyncio.sleep(backoff_time)
        retries += 1
        backoff_time = min(MAX_BACKOFF_S, backoff_time * 2) + random.uniform(0, 1)

    print(f"[Stream {request_id}] Failed after {MAX_RETRIES} retries.")
    return None

async def main():
    print(f"--- Sending {len(payloads)} concurrent streaming requests using aiohttp with backoff ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print(f"Max Retries: {MAX_RETRIES}, Initial Backoff: {INITIAL_BACKOFF_S}s")
    print("---")

    start_time = time.time()
    # Limit concurrency slightly to reduce initial burst, adjust as needed
    semaphore = asyncio.Semaphore(3) 
    
    async def run_with_semaphore(coro):
        async with semaphore:
            return await coro

    async with aiohttp.ClientSession() as session:
        tasks = [
            run_with_semaphore(make_streaming_request_with_backoff(session, chat_completions_url, headers, payload, i+1))
            for i, payload in enumerate(payloads)
        ]
        results = await asyncio.gather(*tasks) # Run tasks concurrently

    end_time = time.time()
    successful_results = [r for r in results if r is not None]
    print(f"\n--- All concurrent streams with backoff finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    print(f"Successful streams: {len(successful_results)}/{len(payloads)}")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 