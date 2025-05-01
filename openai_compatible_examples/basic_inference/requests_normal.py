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
# API key is fetched dynamically before each request
base_headers = {
    "Content-Type": "application/json",
}

# Define the payload
data = {
    "model": model_name,
    "messages": [
        {"role": "user", "content": "Hello! Can you tell me a short joke?"}
    ],
    "max_tokens": 50,
    "temperature": 0.7
}

def main():
    print("--- Sending normal request using requests library ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print("---")

    try:
        # Fetch the latest API key
        current_api_key = get_api_key()
        headers = {**base_headers, "Authorization": f"Bearer {current_api_key}"}

        # Send the POST request
        response = requests.post(chat_completions_url, headers=headers, json=data, timeout=60)

        # Check for successful response
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)

        # Parse the JSON response
        response_json = response.json()

        print("--- Full Response ---")
        print(json.dumps(response_json, indent=2))
        print("---")

        # Extract and print the message content
        if "choices" in response_json and len(response_json["choices"]) > 0:
            first_choice = response_json["choices"][0]
            if "message" in first_choice and "content" in first_choice["message"]:
                message_content = first_choice["message"]["content"]
                print(f"Assistant's Response: {message_content}")
            else:
                print("Could not find message content in the response.")
        else:
            print("No choices found in the response.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 