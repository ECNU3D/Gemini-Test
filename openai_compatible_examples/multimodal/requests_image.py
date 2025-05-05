import os
import sys
import requests
import json
import copy
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

# Get API details and image path from environment variables
api_base = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
# Use a model known to support vision, or a default if not specified
model_name = os.getenv("MODEL_NAME", "default-vision-model")
image_path = os.getenv("IMAGE_PATH")

if not api_base:
    raise ValueError("OPENAI_API_BASE environment variable not set.")
if not image_path or not os.path.exists(image_path):
    raise ValueError(f"Image path '{image_path}' not found or not set in .env (IMAGE_PATH).")

print(f"--- Preparing multimodal request --- ")
print(f"API Base: {api_base}")
print(f"Model: {model_name}")
print(f"Image Path: {image_path}")

# Encode the image
try:
    base64_image_data_uri = encode_image_to_base64(image_path)
    # persist the base64_image_data_uri to a file
    with open("base64_image_data_uri_2.txt", "w") as f:
        f.write(base64_image_data_uri)

    print(f"Successfully encoded image (truncated): {base64_image_data_uri[:80]}...")
except (FileNotFoundError, ValueError) as e:
    print(f"Error encoding image: {e}")
    sys.exit(1) # Exit if image encoding fails
except Exception as e:
    print(f"An unexpected error occurred during image encoding: {e}")
    sys.exit(1)

print("---")

# Define the endpoint URL
chat_completions_url = f"{api_base.rstrip('/')}/chat/completions"

# Define headers
headers = {
    "Content-Type": "application/json",
}

# Define the payload using the OpenAI vision format
data = {
    "model": model_name,
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is in this image? Describe it briefly."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"{base64_image_data_uri}" # Pass the raw content
                    }
                }
            ]
        }
    ],
    "max_tokens": 100 # Adjust max_tokens as needed for image descriptions
}


print(f"--- Sending multimodal request to: {chat_completions_url} ---")
# Avoid printing the full base64 string in the payload log
payload_log = copy.deepcopy(data)
# Use the original data URI for logging if needed, or adjust logging as preferred
payload_log["messages"][0]["content"][1]["image_url"]["url"] = f"{base64_image_data_uri[:50]}...<truncated>"
print(f"Payload (image truncated): {json.dumps(payload_log, indent=2)}")
print("---")

def main():
    global headers
    try:
        # Fetch the latest API key
        current_api_key = get_api_key()
        headers = {**headers, "Authorization": f"Bearer {current_api_key}"}

        # Send the POST request
        response = requests.post(chat_completions_url, headers=headers, json=data, timeout=120)

        response.raise_for_status()

        # Parse the JSON response
        response_json = response.json()

        print("--- Full API Response ---")
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
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 