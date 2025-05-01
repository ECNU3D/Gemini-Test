import os
import asyncio
import aiohttp
import json
import time
from dotenv import load_dotenv
from utils.auth_helpers import get_api_key_async # Use async version

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Default to a dummy key if not set
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

# Define the endpoint URL
chat_completions_url = f"{api_base.rstrip('/')}/chat/completions"

# Define headers
base_headers = {
    "Content-Type": "application/json",
}

# Define multiple payloads for concurrent requests
payloads = [
    {
        "model": model_name,
        "messages": [{"role": "user", "content": f"Tell me joke #{i+1}"}],
        "max_tokens": 50,
        "temperature": 0.7 + i*0.1 # Vary temperature slightly
    } for i in range(3) # Create 3 concurrent requests
]

async def send_request(session, url, payload, request_id):
    task_start_time = time.time()
    print(f"[Request {request_id}] Starting...")
    try:
        # Fetch the latest API key asynchronously
        current_api_key = await get_api_key_async()
        headers = {**base_headers, "Authorization": f"Bearer {current_api_key}"}

        async with session.post(url, headers=headers, json=payload, timeout=60) as response:
            response_data = await response.json()
            response.raise_for_status() # Raise an exception for bad status codes
            print(f"[Request {request_id}] Status: {response.status}")
            print(f"[Request {request_id}] Received Response: {json.dumps(response_data, indent=2)}")
            return response_data
    except Exception as e:
        print(f"[Request {request_id}] Error: {e}")
        return None

async def main():
    # Updated print statement
    print(f"--- Sending {len(payloads)} concurrent normal (non-streaming) requests using aiohttp ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print("---")

    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [
            send_request(session, chat_completions_url, payload, i+1)
            for i, payload in enumerate(payloads)
        ]
        results = await asyncio.gather(*tasks) # Run tasks concurrently

    end_time = time.time()
    print("--- All concurrent requests finished ---")
    print(f"Total time: {end_time - start_time:.2f} seconds")
    # You can process 'results' list here if needed

if __name__ == "__main__":
    # For Windows compatibility with asyncio in some environments
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main()) 