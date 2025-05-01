import os
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

def main():
    print("--- Sending streaming request using OpenAI SDK ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print("---")

    try:
        # Initialize client - API key is fetched dynamically *per request* below
        client = OpenAI(
            base_url=api_base_url,
            api_key="temp-key" # Initial key, will be replaced
        )

        # Fetch the latest API key and update the client
        client.api_key = get_api_key()

        # Define the messages payload
        messages = [
            {"role": "user", "content": "Write a short poem about the moon."}
        ]

        print(f"Messages: {messages}")
        print("---")
        print("Assistant's Response (streaming):")

        full_response_content = ""
        # Make the API call with stream=True
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            stream=True, # Enable streaming
        )

        # Iterate over the stream chunks
        for chunk in stream:
            # Check if the chunk has content in the delta
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                content_part = chunk.choices[0].delta.content
                print(content_part, end='', flush=True) # Print part as it arrives
                full_response_content += content_part
            # You might also want to check for finish_reason if needed
            # if chunk.choices and chunk.choices[0].finish_reason:
            #    print(f"\nStream finished with reason: {chunk.choices[0].finish_reason}")

        print("\n\n--- Stream finished ---")
        # Optional: print the full assembled response
        # print("\n--- Full Assembled Response ---")
        # print(full_response_content)
        # print("---")

    except APIError as e:
        # Handle API errors
        print(f"\nAn API error occurred: {e}")
        print(f"Status Code: {e.status_code}")
        print(f"Response: {e.response}")
    except Exception as e:
        # Handle other potential errors
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 