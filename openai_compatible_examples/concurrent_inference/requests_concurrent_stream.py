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

from utils.auth_helpers import get_api_key_async

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
    "Accept": "text/event-stream" # Important for streaming
}

payloads = [
    {
        "model": model_name,
        "messages": [{"role": "user", "content": f"Write a short poem #{i+1}"}],
        "max_tokens": 60,
        "temperature": 0.6 + i*0.1,
        "stream": True # Enable streaming
    } for i in range(3) # Create 3 concurrent requests
]

async def process_stream(response, request_id):
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
                            print(content_piece, end="", flush=True) # Print delta immediately
                            full_content += content_piece
                except json.JSONDecodeError:
                    print(f"\n[Stream {request_id}] Warning: Received non-JSON data: {data_content}")
            elif line_str: # Handle potential empty lines or other data
                print(f"\n[Stream {request_id}] Received non-SSE line: {line_str}")

    except aiohttp.ClientPayloadError as e: # More specific error for payload issues
        print(f"\n[Stream {request_id}] Payload Error during stream processing: {e}")
    except Exception as e:
        print(f"\n[Stream {request_id}] Error processing stream: {e}")
    finally:
        print(f"[Stream {request_id}] Final content length: {len(full_content)}")
        return full_content

async def make_streaming_request(session, url, headers, payload, request_id):
    print(f"[Stream {request_id}] Starting...")

    try:
        # Fetch the latest API key asynchronously
        current_api_key = await get_api_key_async()
        headers = {**headers, "Authorization": f"Bearer {current_api_key}"}

        # Get proxy from environment variables
        http_proxy = os.getenv("HTTP_PROXY")
        https_proxy = os.getenv("HTTPS_PROXY")

        # Determine which proxy to use based on the URL scheme
        proxy_to_use = None
        if url.startswith("https://") and https_proxy:
            proxy_to_use = https_proxy
        elif url.startswith("http://") and http_proxy:
            proxy_to_use = http_proxy

        # Use timeout=None for streaming requests potentially lasting longer
        async with session.post(url, headers=headers, json=payload, timeout=None, proxy=proxy_to_use) as response:
            response.raise_for_status() # Check for HTTP errors early
            print(f"[Stream {request_id}] Connection successful (Status: {response.status})")
            result = await process_stream(response, request_id)
            return result
    except aiohttp.ClientResponseError as e: # Specific handling for HTTP status errors
        print(f"\n[Stream {request_id}] HTTP Error: Status {e.status} - {e.message}")
        try:
            # Attempt to read the error body for more context
            error_body = await response.text()
            print(f"[Stream {request_id}] Error Body: {error_body[:500]}") # Log first 500 chars
        except Exception as read_err:
            print(f"[Stream {request_id}] Could not read error body: {read_err}")
        return None
    except aiohttp.ClientConnectionError as e:
        print(f"\n[Stream {request_id}] Connection Error: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"\n[Stream {request_id}] Request timed out.") # Specific timeout message
        return None
    except Exception as e: # Catch other potential errors
        print(f"\n[Stream {request_id}] An unexpected error occurred: {e}")
        return None

async def main():
    print(f"--- Sending {len(payloads)} concurrent streaming requests using aiohttp ---")
    print(f"Base URL: {api_base}")
    print(f"Model: {model_name}")
    print("---")

    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [
            make_streaming_request(session, chat_completions_url, headers, payload, i+1)
            for i, payload in enumerate(payloads)
        ]
        results = await asyncio.gather(*tasks) # Run tasks concurrently

    end_time = time.time()
    print(f"\n--- All concurrent streams finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    # Add count of successful requests
    successful_results = [res for res in results if res is not None]
    print(f"Successfully completed {len(successful_results)} streams.")
    # Results contains the full text from each stream (or None if error)
    # print(f"Aggregated results: {results}")
    # raise error if there are any failed requests
    if len(successful_results) != len(payloads):
        raise Exception("Failed to complete all requests.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 