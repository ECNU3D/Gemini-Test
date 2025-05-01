import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from utils.auth_helpers import get_api_key

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base = os.getenv("OPENAI_API_BASE")
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

# Define the endpoint URL
chat_completions_url = f"{api_base.rstrip('/')}/chat/completions"

# Define headers
base_headers = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream" # Important for streaming
}

# Define the payload, adding stream=True
data = {
    "model": model_name,
    "messages": [
        {"role": "user", "content": "Write a short story about a friendly robot. Keep it under 100 words."}
    ],
    "max_tokens": 150,
    "temperature": 0.7,
    "stream": True # Enable streaming
}

def main():
    print("--- Sending streaming request using requests library ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print("---")

    try:
        # Fetch the latest API key
        current_api_key = get_api_key()
        headers = {**base_headers, "Authorization": f"Bearer {current_api_key}"}

        # Send the POST request with stream=True
        with requests.post(chat_completions_url, headers=headers, json=data, stream=True, timeout=60) as response:
            # Raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()

            print("Response Headers:", response.headers)
            print("\nStreaming Response Body:")

            full_response_content = ""

            # Iterate over the stream
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    # OpenAI streams use Server-Sent Events (SSE)
                    # Lines usually start with "data: "
                    if decoded_line.startswith('data: '):
                        content = decoded_line[len('data: '):]
                        # Check for the stream termination signal
                        if content.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(content)
                            if chunk.get("choices") and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content_part = delta.get("content")
                                if content_part:
                                    print(content_part, end='', flush=True) # Print part as it arrives
                                    full_response_content += content_part
                        except json.JSONDecodeError:
                            print(f"\nError decoding JSON chunk: {content}")
                            continue # Continue processing next line
                    elif decoded_line.strip(): # Print other non-empty lines for debugging
                        print(f"\nReceived non-data line: {decoded_line}")

            print("\n\n--- Stream finished ---")
            # Optional: print the full assembled response
            # print("\n--- Full Assembled Response ---")
            # print(full_response_content)
            # print("---")

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred during the streaming request: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 