import os
import requests
import json
import sys
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

# Define the payload, requesting JSON output
# Note: The prompt explicitly asks for JSON output.
# The 'response_format' parameter signals the API to enforce JSON output.
data = {
    "model": model_name,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant designed to output JSON."
        },
        {
            "role": "user",
            "content": "Extract the name, age, and city from the following sentence: \"Alice, aged 25, lives in Wonderland.\" Respond ONLY with a valid JSON object."
        }
    ],
    "response_format": { "type": "json_object" }, # Request JSON mode
    "max_tokens": 100,
    "temperature": 0.5
}

print(f"--- Sending request for JSON response to: {chat_completions_url} ---")
print(f"Payload: {json.dumps(data, indent=2)}")
print("---")

def main():
    global headers
    print("--- Sending JSON mode request using requests library ---")
    print(f"Target URL: {chat_completions_url}")
    print(f"Model: {model_name}")
    print("NOTE: Ensure your prompt instructs the model to output JSON.")
    print("---")

    try:
        # Fetch the latest API key
        current_api_key = get_api_key()
        headers = {**headers, "Authorization": f"Bearer {current_api_key}"}

        # Send the POST request
        response = requests.post(chat_completions_url, headers=headers, json=data, timeout=60)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Parse the JSON response from the API call itself
        response_api_json = response.json()

        print("--- Full API Response ---")
        print(json.dumps(response_api_json, indent=2))
        print("---")

        # Extract the message content, which should be a JSON string
        if "choices" in response_api_json and len(response_api_json["choices"]) > 0:
            first_choice = response_api_json["choices"][0]
            if "message" in first_choice and "content" in first_choice["message"]:
                message_content_str = first_choice["message"]["content"]
                print(f"Assistant's raw content (should be JSON string):\n{message_content_str}")
                print("---")
                # Attempt to parse the message content string as JSON
                try:
                    parsed_content_json = json.loads(message_content_str)
                    print("Parsed JSON content from Assistant:")
                    print(json.dumps(parsed_content_json, indent=2))
                except json.JSONDecodeError:
                    print("Could not parse the assistant's message content as JSON.")
            else:
                print("Could not find message content in the response.")
        else:
            print("No choices found in the response.")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 