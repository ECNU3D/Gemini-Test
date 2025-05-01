import os
import asyncio
import time
from openai import AsyncOpenAI, APIError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
model_name = os.getenv("MODEL_NAME", "default-model")

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

# Configure the Async OpenAI client
aclient = AsyncOpenAI(
    base_url=api_base_url,
    api_key=api_key,
)

# Define multiple message sets for concurrent requests
all_messages = [
    [
        {"role": "user", "content": f"Write a short story {i+1} about a brave knight"}
    ],
    [
        {"role": "user", "content": f"Write a short story {i+1} about a clever fox"}
    ],
    [
        {"role": "user", "content": f"Write a short story {i+1} about a lonely robot"}
    ]
]

async def process_openai_stream(stream, request_id):
    print(f"[Stream {request_id}] Receiving data...")
    full_content = ""
    try:
        async for chunk in stream:
            content_piece = chunk.choices[0].delta.content or ""
            if content_piece:
                print(f"[Stream {request_id}] {content_piece}", end="", flush=True)
                full_content += content_piece
        print(f"\n[Stream {request_id}] Stream finished.") # Newline after stream finishes
    except APIError as e:
        print(f"\n[Stream {request_id}] OpenAI API Error during stream: {e}")
    except Exception as e:
        print(f"\n[Stream {request_id}] An unexpected error occurred during stream: {e}")
    finally:
        print(f"[Stream {request_id}] Final content length: {len(full_content)}")
        return full_content

async def make_openai_streaming_request(messages, request_id):
    print(f"[Stream {request_id}] Sending request...")
    try:
        stream = await aclient.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            stream=True
        )
        # Process the stream in this task
        result = await process_openai_stream(stream, request_id)
        return result
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
        make_openai_streaming_request(messages, i+1)
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


if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 