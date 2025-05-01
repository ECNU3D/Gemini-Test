"""
Example of sending multiple images to an OpenAI-compatible Chat Completions
endpoint that supports vision models, using the 'requests' library.

Requires a model capable of processing image inputs (vision model).
Assumes the API follows the content array format for multimodal inputs.
"""

import os
import json
import requests
from dotenv import load_dotenv

# Assuming image_helpers.py exists in ../utils
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
try:
    from image_helpers import image_to_base64_data_url
except ImportError:
    print("Error: image_helpers.py not found. Please ensure it's in the 'utils' directory.")
    # Define a dummy function if import fails, to allow script structure check
    def image_to_base64_data_url(image_path):
        print(f"[Dummy] Pretending to encode: {image_path}")
        return "data:image/jpeg;base64,DUMMY_BASE64_DATA"

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
# Ensure MODEL_NAME is set to a vision-capable model in your .env file
MODEL_NAME = os.getenv("MODEL_NAME")

# Paths to your sample image files (NEEDS TO EXIST or be placeholder)
IMAGE_PATH_1 = os.getenv("IMAGE_PATH", "example.jpg") # Reuse existing env var or set directly
IMAGE_PATH_2 = "example_2.jpg" # Path to a second image (create or replace)

# Optional: Direct URL to an image instead of local file
IMAGE_URL_3 = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

CHAT_COMPLETIONS_URL = f"{API_BASE_URL}/chat/completions"

# --- Prepare Image Data ---
image_data_1 = None
image_data_2 = None

if IMAGE_PATH_1 and os.path.exists(IMAGE_PATH_1):
    image_data_1 = image_to_base64_data_url(IMAGE_PATH_1)
    print(f"Encoded image 1 ({IMAGE_PATH_1}) to base64 data URL.")
elif IMAGE_PATH_1:
    print(f"Warning: Image path 1 '{IMAGE_PATH_1}' not found. Skipping.")

if os.path.exists(IMAGE_PATH_2):
    image_data_2 = image_to_base64_data_url(IMAGE_PATH_2)
    print(f"Encoded image 2 ({IMAGE_PATH_2}) to base64 data URL.")
else:
    print(f"Warning: Image path 2 '{IMAGE_PATH_2}' not found. Ensure this file exists.")
    # Provide placeholder if needed for testing structure
    # image_data_2 = "data:image/png;base64,PLACEHOLDER_DATA"

# --- API Request --- 
# Construct the message list with multiple multimodal inputs
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": "What are in these images? Compare the scenes."
            },
        ]
    }
]

# Add image 1 (if available)
if image_data_1:
    messages[0]["content"].append(
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_1 # Base64 Data URL
                # "detail": "high" # Optional: low, high, auto
            }
        }
    )

# Add image 2 (if available)
if image_data_2:
     messages[0]["content"].append(
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_2 # Base64 Data URL
            }
        }
    )

# Add image 3 (from URL)
messages[0]["content"].append(
    {
        "type": "image_url",
        "image_url": {
            "url": IMAGE_URL_3 # Direct URL
        }
    }
)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

payload = {
    "model": MODEL_NAME, # Must be a vision model
    "messages": messages,
    "max_tokens": 300, # Adjust as needed
}
payload = {k: v for k, v in payload.items() if v is not None}

if not MODEL_NAME:
    print("Error: MODEL_NAME environment variable must be set to a vision model.")
else:
    print(f"--- Sending request with multiple images to: {CHAT_COMPLETIONS_URL} ---")
    # Avoid printing full base64 data in payload log
    log_payload = json.loads(json.dumps(payload))
    for msg in log_payload.get("messages", []):
        if isinstance(msg.get("content"), list):
            for item in msg["content"]:
                if item.get("type") == "image_url" and item.get("image_url", {}).get("url", "").startswith("data:"):
                    item["image_url"]["url"] = item["image_url"]["url"][:50] + "...[TRUNCATED BASE64]..."
    print(f"Payload Structure:
{json.dumps(log_payload, indent=2)}")
    print("-" * 30)

    try:
        response = requests.post(CHAT_COMPLETIONS_URL, headers=headers, json=payload)
        response.raise_for_status()

        response_data = response.json()
        print(f"--- Full API Response ---")
        print(json.dumps(response_data, indent=2))
        print("-" * 30)

        if response_data.get("choices"):
            assistant_message = response_data["choices"][0]["message"]["content"]
            print(f"Assistant Message:
{assistant_message}")
        else:
            print("No 'choices' found in the response.")

    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")
        if e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            try:
                print(f"Response Body: {e.response.text}")
            except Exception:
                print("Could not print response body.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

print("-" * 30)
print("Multi-image request example complete.") 