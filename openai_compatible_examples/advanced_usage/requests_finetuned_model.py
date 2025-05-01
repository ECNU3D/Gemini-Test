"""
Example of using a specific fine-tuned model ID with the OpenAI-compatible
Chat Completions endpoint using the 'requests' library.

Assumes you have already fine-tuned a model and have its ID.
Set the FINE_TUNED_MODEL_NAME environment variable to your model ID.
"""

import os
import json
import requests
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")

# --- !! Specify Your Fine-Tuned Model ID Here !! ---
# Load from environment variable or set directly
FINE_TUNED_MODEL_ID = os.getenv("FINE_TUNED_MODEL_NAME")

CHAT_COMPLETIONS_URL = f"{API_BASE_URL}/chat/completions"

# --- API Request ---
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

# Example conversation (adjust prompt based on your fine-tuning task)
messages = [
    {"role": "system", "content": "You are a helpful assistant fine-tuned for a specific task."},
    {"role": "user", "content": "Generate a response in the style you were trained on."}
]

payload = {
    "model": FINE_TUNED_MODEL_ID, # Specify the fine-tuned model ID here
    "messages": messages,
    "max_tokens": 100,
    "temperature": 0.7,
}

# Remove None values from payload (important if FINE_TUNED_MODEL_ID is None)
payload = {k: v for k, v in payload.items() if v is not None}

if not FINE_TUNED_MODEL_ID:
    print("Error: FINE_TUNED_MODEL_NAME environment variable is not set.")
    print("Please set it to your fine-tuned model ID to run this example.")
else:
    print(f"--- Sending request to: {CHAT_COMPLETIONS_URL} ---")
    print(f"Using Fine-Tuned Model: {FINE_TUNED_MODEL_ID}")
    print(f"Payload:
{json.dumps(payload, indent=2)}")
    print("-" * 30)

    try:
        response = requests.post(CHAT_COMPLETIONS_URL, headers=headers, json=payload)
        response.raise_for_status() # Raise an exception for bad status codes

        response_data = response.json()
        print(f"--- Full API Response ---")
        print(json.dumps(response_data, indent=2))
        print("-" * 30)

        # --- Response Handling ---
        if response_data.get("choices"):
            assistant_message = response_data["choices"][0]["message"]["content"]
            print(f"Assistant Message (from fine-tuned model):")
            print(assistant_message)
        else:
            print("No 'choices' found in the response.")

    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")
        if e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            try:
                # Check if the error is specifically about the model not found
                error_info = e.response.json()
                if e.response.status_code == 404 and "model_not_found" in error_info.get("error", {}).get("code", ""):
                     print(f"Error: Fine-tuned model '{FINE_TUNED_MODEL_ID}' not found on the endpoint.")
                else:
                    print(f"Response Body: {e.response.text}")
            except Exception:
                print("Could not print/parse response body.")
    except KeyError as e:
        print(f"Error accessing expected key in API response: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

print("-" * 30)
print("Fine-tuned model request example complete.") 