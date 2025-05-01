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

# Load environment variables from .env file
load_dotenv()

# Get API details and image path from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
# Use a model known to support vision, or a default if not specified
model_name = os.getenv("MODEL_NAME", "default-vision-model")
image_path = os.getenv("IMAGE_PATH")

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")
if not image_path:
    raise ValueError("IMAGE_PATH environment variable not set. Please provide a path to an image file.")

print(f"--- Preparing multimodal request (OpenAI SDK) --- ")
print(f"API Base: {api_base_url}")
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

# Configure the OpenAI client
client = OpenAI(
    base_url=api_base_url,
    api_key=api_key,
)

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
                    "url": base64_image_url,
                    # Optional: detail level (low, high, auto) - defaults to auto
                    # "detail": "high"
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

try:
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