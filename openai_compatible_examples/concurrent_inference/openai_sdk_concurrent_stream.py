import os
import asyncio
import time
import sys
from openai import AsyncOpenAI, APIError
from openai.types.chat import ChatCompletionChunk # For type hinting
from dotenv import load_dotenv

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key_async # Use async version

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
model_name = os.getenv("MODEL_NAME", "default-model")

REQUEST_TIMEOUT = 60  # Timeout in seconds (1 minute)

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

# Initialize client - API key fetched per request/stream
# aclient = AsyncOpenAI(
#     base_url=api_base_url,
#     api_key=api_key
# )

# Define multiple message sets for concurrent requests
all_messages = [
    [
        {"role": "user", "content": "Write a short story about a brave knight"}
    ],
    [
        {"role": "user", "content": "Write a short story about a clever fox"}
    ],
    [
        {"role": "user", "content": "Write a short story about a lonely robot"}
    ]
]

async def process_openai_stream(stream, request_id):
    print(f"[Stream {request_id}] Receiving data...")
    full_content = ""
    try:
        async for chunk in stream:
            content_piece = chunk.choices[0].delta.content or ""
            if content_piece:
                print(f"\n[Stream {request_id}] {content_piece}", end="", flush=True)
                full_content += content_piece
        print(f"\n[Stream {request_id}] Stream finished.") # Newline after stream finishes
    except APIError as e:
        print(f"\n[Stream {request_id}] OpenAI API Error during stream: {e}")
    except Exception as e:
        print(f"\n[Stream {request_id}] An unexpected error occurred during stream: {e}")
    finally:
        print(f"[Stream {request_id}] Final content length: {len(full_content)}")
        return full_content

async def run_openai_stream(messages, request_id):
    print(f"[Stream {request_id}] Starting...")
    full_content = ""
    try:
        # Initialize client within the task to fetch the latest key
        aclient = AsyncOpenAI(
            base_url=api_base_url,
            api_key=await get_api_key_async()
        )

        async def stream_with_processing():
            stream = await aclient.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=100,
                temperature=0.7,
                stream=True
            )
            # Process the stream in this task
            return await process_openai_stream(stream, request_id)

        result = await asyncio.wait_for(stream_with_processing(), timeout=REQUEST_TIMEOUT)
        return result
    except asyncio.TimeoutError:
        print(f"\n[Stream {request_id}] Timed out after {REQUEST_TIMEOUT} seconds.")
    except APIError as e:
        print(f"\n[Stream {request_id}] OpenAI API Error on create: {e}")
    except Exception as e:
        print(f"\n[Stream {request_id}] An unexpected error occurred on create: {e}")
    return None

async def main():
    print(f"--- Sending {len(all_messages)} concurrent streaming requests using OpenAI SDK ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print("---")

    start_time = time.time()

    tasks = [
        run_openai_stream(messages, i+1)
        for i, messages in enumerate(all_messages)
    ]
    results = await asyncio.gather(*tasks) # Run tasks concurrently

    end_time = time.time()
    print(f"\n--- All concurrent streams finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    # Results contains the full text from each stream (or None if error)
    # print(f"Aggregated results: {results}")
    successful_results = [res for res in results if res is not None]
    print(f"Successfully completed {len(successful_results)} streams.")
    print("--- Successful Stream Responses ---")
    for i, response in enumerate(successful_results):
        print(f"Response {i+1}:\n{response}\n---")
    # raise error if there are any failed requests
    if len(successful_results) != len(all_messages):
        raise Exception("Failed to complete all requests.")


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 