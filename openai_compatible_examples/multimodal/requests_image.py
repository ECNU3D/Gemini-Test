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

from utils.image_helpers import encode_image_to_base64

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
if not image_path:
    raise ValueError("IMAGE_PATH environment variable not set. Please provide a path to an image file.")

print(f"--- Preparing multimodal request --- ")
print(f"API Base: {api_base}")
print(f"Model: {model_name}")
print(f"Image Path: {image_path}")

# Encode the image
try:
    base64_image_url = encode_image_to_base64(image_path)
    print(f"Successfully encoded image (truncated): {base64_image_url[:80]}...")
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
    "Authorization": f"Bearer {api_key}"
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
                        "url": base64_image_url
                    }
                }
            ]
        }
    ],
    "max_tokens": 100 # Adjust max_tokens as needed for image descriptions
}

print(f"--- Sending multimodal request to: {chat_completions_url} ---")
# Avoid printing the full base64 string in the payload log
payload_log = data.copy()
payload_log["messages"][0]["content"][1]["image_url"]["url"] = f"{base64_image_url[:50]}...<truncated>"
print(f"Payload (image truncated): {json.dumps(payload_log, indent=2)}")
print("---")

try:
    # Make the POST request
    response = requests.post(chat_completions_url, headers=headers, json=data)

    # Check for successful response
    response.raise_for_status() # Raises an HTTPError for bad responses

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