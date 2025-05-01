import os
import asyncio
import time
from openai import AsyncOpenAI, APIError # Import AsyncOpenAI
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
        {"role": "user", "content": f"Explain concept {i+1} simply: Quantum Entanglement"}
    ],
    [
        {"role": "user", "content": f"Explain concept {i+1} simply: Blockchain"}
    ],
    [
        {"role": "user", "content": f"Explain concept {i+1} simply: General Relativity"}
    ]
]

async def make_openai_request(messages, request_id):
    print(f"[Request {request_id}] Sending...")
    try:
        response = await aclient.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            stream=False
        )
        print(f"[Request {request_id}] Received Response:")
        print(f"[Request {request_id}] {response.choices[0].message.content.strip()}")
        return response
    except APIError as e:
        print(f"[Request {request_id}] OpenAI API Error: {e}")
    except Exception as e:
        print(f"[Request {request_id}] An unexpected error occurred: {e}")
    return None

async def main():
    # Updated print statement
    print(f"--- Sending {len(all_messages)} concurrent normal (non-streaming) requests using OpenAI SDK ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print("---")

    start_time = time.time()

    tasks = [
        make_openai_request(messages, i+1)
        for i, messages in enumerate(all_messages)
    ]
    results = await asyncio.gather(*tasks) # Run tasks concurrently

    end_time = time.time()
    print("--- All concurrent requests finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    # Filter out None results from errors
    successful_results = [res for res in results if res is not None]
    print(f"Successfully completed {len(successful_results)} requests.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 