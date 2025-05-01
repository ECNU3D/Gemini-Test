import os
import asyncio
import aiohttp
import json
import time
from dotenv import load_dotenv

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
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
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

async def make_request(session, url, headers, payload, request_id):
    print(f"[Request {request_id}] Sending...")
    async with session.post(url, headers=headers, json=payload) as response:
        print(f"[Request {request_id}] Status: {response.status}")
        response_json = await response.json()
        print(f"[Request {request_id}] Received Response: {json.dumps(response_json, indent=2)}")
        return response_json

async def main():
    # Updated print statement
    print(f"--- Sending {len(payloads)} concurrent normal (non-streaming) requests using aiohttp ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print("---")

    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [
            make_request(session, chat_completions_url, headers, payload, i+1)
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