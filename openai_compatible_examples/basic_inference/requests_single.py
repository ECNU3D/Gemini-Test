import os
import requests
import json
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

# Define the payload
data = {
    "model": model_name,
    "messages": [
        {"role": "user", "content": "Hello! Can you tell me a short joke?"}
    ],
    "max_tokens": 50,
    "temperature": 0.7
}

print(f"--- Sending request to: {chat_completions_url} ---")
print(f"Payload: {json.dumps(data, indent=2)}")
print("---")

try:
    # Make the POST request
    response = requests.post(chat_completions_url, headers=headers, json=data)

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