import os
import sys
from openai import OpenAI
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
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Default to a dummy key if not set
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

print(f"--- Configuring OpenAI SDK ---")
print(f"Base URL: {api_base_url}")
print(f"Model: {model_name}")
print("API Key: Using provided key (or dummy key)")
print("---")

# Define the messages payload
messages = [
    {"role": "user", "content": "Hello! Can you explain the concept of API compatibility briefly?"}
]

def main():
    print("--- Sending normal request using OpenAI SDK ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print("---")

    try:
        # Initialize client - API key is fetched dynamically *per request* below
        # We could initialize here, but updating per-request is safer for expiry
        client = OpenAI(
            base_url=api_base_url,
            api_key="temp-key" # Initial key, will be replaced
        )

        # Fetch the latest API key and update the client
        client.api_key = get_api_key()

        # Send the request
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=100,
            temperature=0.7,
        )

        print("--- Full Response Object ---")
        # The response object is a Pydantic model, print its dict representation
        print(chat_completion.model_dump_json(indent=2))
        print("---")

        # Extract and print the message content
        if chat_completion.choices:
            message = chat_completion.choices[0].message
            if message and message.content:
                print(f"Assistant's Response: {message.content}")
            else:
                print("Could not find message content in the response.")
        else:
            print("No choices found in the response.")

    except Exception as e:
        # Handle other potential errors
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()