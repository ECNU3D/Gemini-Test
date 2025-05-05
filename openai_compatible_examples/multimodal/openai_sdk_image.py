import os
import sys
from openai import OpenAI, APIError
from dotenv import load_dotenv

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.image_helpers import encode_image_to_base64
from utils.auth_helpers import get_api_key

# Load environment variables from .env file
load_dotenv()

# Get API details, image path, and model name from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
image_path = os.getenv("IMAGE_PATH")
model_name = os.getenv("MODEL_NAME", "gpt-4-vision-preview") # Default if not set

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")
if not image_path or not os.path.exists(image_path):
    raise ValueError(f"Image path '{image_path}' not found or not set in .env (IMAGE_PATH).")

print(f"--- Preparing multimodal request (OpenAI SDK) --- ")
print(f"API Base: {api_base_url}")
print(f"Image Path: {image_path}")
print(f"Model Name: {model_name}")

def main():
    print("--- Sending image request using OpenAI SDK ---")
    print(f"Base URL: {api_base_url}")
    print(f"Image Path: {image_path}")
    print(f"Model Name: {model_name}")
    print("---")

    # Encode the image
    base64_image_data_uri = encode_image_to_base64(image_path)
    if not base64_image_data_uri:
        print("Error encoding image.")
        return

    try:
        # Initialize client - API key is fetched dynamically *per request* below
        client = OpenAI(
            base_url=api_base_url,
            api_key="temp-key" # Placeholder, will be replaced
        )

        # Fetch the latest API key and update the client
        client.api_key = get_api_key()

        # Define the payload using the structure expected by the OpenAI SDK
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image_data_uri
                        }
                    }
                ]
            }
        ]

        print("--- Sending multimodal request using OpenAI SDK ---")
        # Avoid printing the full base64 string in logs
        messages_log = []
        for m in messages:
            content_log = []
            for c in m["content"]:
                if c["type"] == "text":
                    content_log.append(c)
                else:
                    # Ensure image_url and url exist before trying to access them
                    image_url_data = c.get("image_url", {})
                    original_url = image_url_data.get("url", "")
                    truncated_url = f"{original_url[:50]}...<truncated>"
                    content_log.append({"type": "image_url", "image_url": {"url": truncated_url}})
            messages_log.append({"role": m["role"], "content": content_log})

        print(f"Messages (image truncated): {messages_log}")
        print("---")

        # Make the API call
        chat_completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=150 # Adjust as needed
        )

        print("--- Full API Response Object ---")
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

    except APIError as e:
        # Handle API errors
        print(f"An API error occurred: {e}")
        print(f"Status Code: {e.status_code}")
        print(f"Response: {e.response}")
    except Exception as e:
        # Handle other potential errors
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 