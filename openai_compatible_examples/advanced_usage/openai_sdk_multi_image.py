"""
Example of sending multiple images to an OpenAI-compatible Chat Completions
endpoint that supports vision models, using the 'openai' Python SDK.

Requires a model capable of processing image inputs (vision model).
"""

import os
import json 
import sys
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# Assuming image_helpers.py exists in ../utils
# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key # Use async version
from utils.image_helpers import encode_image_to_base64
# --- Configuration ---
load_dotenv() # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = get_api_key()
# Ensure MODEL_NAME is set to a vision-capable model in your .env file
MODEL_NAME = os.getenv("MODEL_NAME")

# Paths to your sample image files (NEEDS TO EXIST or be placeholder)
IMAGE_PATH_1 = os.getenv("IMAGE_PATH", "example.jpg") # Reuse existing env var or set directly
IMAGE_PATH_2 = "example_2.jpg" # Path to a second image (create or replace)

# Optional: Direct URL to an image instead of local file
IMAGE_URL_3 = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"

# --- Initialize OpenAI Client ---
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# --- Prepare Image Data ---
image_data_1 = None
image_data_2 = None

if IMAGE_PATH_1 and os.path.exists(IMAGE_PATH_1):
    image_data_1 = encode_image_to_base64(IMAGE_PATH_1)
    print(f"Encoded image 1 ({IMAGE_PATH_1}) to base64 data URL.")
elif IMAGE_PATH_1:
    print(f"Warning: Image path 1 '{IMAGE_PATH_1}' not found. Skipping.")

if os.path.exists(IMAGE_PATH_2):
    image_data_2 = encode_image_to_base64(IMAGE_PATH_2)
    print(f"Encoded image 2 ({IMAGE_PATH_2}) to base64 data URL.")
else:
    print(f"Warning: Image path 2 '{IMAGE_PATH_2}' not found. Ensure this file exists.")

# --- API Request --- 
# Construct the message list for the SDK
content_list = [
    {
        "type": "text",
        "text": "Describe the contents of these images and identify the main subject in each."
    },
]

# Add image 1 (if available)
if image_data_1:
    content_list.append(
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_1, # Base64 Data URL
                # "detail": "high" # Optional: low, high, auto
            }
        }
    )

# Add image 2 (if available)
if image_data_2:
     content_list.append(
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_2 # Base64 Data URL
            }
        }
    )

# Add image 3 (from URL)
content_list.append(
    {
        "type": "image_url",
        "image_url": {
            "url": IMAGE_URL_3 # Direct URL
        }
    }
)

messages = [
    {
        "role": "user",
        "content": content_list
    }
]

if not MODEL_NAME:
    print("Error: MODEL_NAME environment variable must be set to a vision model.")
else:
    print(f"--- Sending request with multiple images using SDK ---")
    # Avoid printing full base64 data in log
    log_messages = json.loads(json.dumps(messages))
    for msg in log_messages:
        if isinstance(msg.get("content"), list):
            for item in msg["content"]:
                if item.get("type") == "image_url" and item.get("image_url", {}).get("url", "").startswith("data:"):
                    item["image_url"]["url"] = item["image_url"]["url"][:50] + "...[TRUNCATED BASE64]..."
    print(f"Messages Structure: \
{json.dumps(log_messages, indent=2)}")
    print("-" * 30)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME, # Must be a vision model
            messages=messages,
            max_tokens=300,
        )

        print("--- Full API Response ---")
        print(completion.model_dump_json(indent=2))
        print("-" * 30)

        assistant_message = completion.choices[0].message.content
        print(f"Assistant Message: \
{assistant_message}")

    except (APIError, RateLimitError, APITimeoutError) as e:
        print(f"An API error occurred: {e}")
        # ... (rest of error handling) ...
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print(f"Type: {type(e)}")

print("-" * 30)
print("Multi-image SDK example complete.") 