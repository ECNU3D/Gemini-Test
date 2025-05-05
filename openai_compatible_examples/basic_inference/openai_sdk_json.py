import os
import json
import sys
from openai import OpenAI, APIError
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

# Define the messages payload, explicitly asking for JSON
messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant designed to output JSON."
    },
    {
        "role": "user",
        "content": "Provide details for a fictional product: Name, Category, and Price. Respond ONLY with a valid JSON object."
    }
]

def main():
    print("--- Sending JSON mode request using OpenAI SDK ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print("NOTE: Ensure your prompt instructs the model to output JSON.")
    print("      And that your server supports response_format.")
    print("---")

    try:
        # Initialize client - API key is fetched dynamically *per request* below
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
            response_format={ "type": "json_object" }, # Request JSON mode
            max_tokens=100,
            temperature=0.5,
        )

        print("--- Full API Response Object ---")
        print(chat_completion.model_dump_json(indent=2))
        print("---")

        # Extract the message content (should be a JSON string)
        if chat_completion.choices:
            message = chat_completion.choices[0].message
            if message and message.content:
                message_content_str = message.content
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

    except APIError as e:
        # Handle API errors
        print(f"An API error occurred: {e}")
        print(f"Status Code: {e.status_code}")
        print(f"Response: {e.response}")
        raise # Re-raise the exception after printing details
    except Exception as e:
        # Handle other potential errors
        print(f"An unexpected error occurred: {e}")
        raise # Also re-raise other unexpected errors

if __name__ == "__main__":
    main() 