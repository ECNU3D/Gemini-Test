"""
Example of using a specific fine-tuned model ID with the OpenAI-compatible
Chat Completions endpoint using the 'openai' Python SDK.

Assumes you have already fine-tuned a model and have its ID.
Set the FINE_TUNED_MODEL_NAME environment variable to your model ID.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError, NotFoundError

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")

# --- !! Specify Your Fine-Tuned Model ID Here !! ---
# Load from environment variable or set directly
FINE_TUNED_MODEL_ID = os.getenv("FINE_TUNED_MODEL_NAME")

# --- Initialize OpenAI Client ---
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# --- API Request ---
# Example conversation (adjust prompt based on your fine-tuning task)
messages = [
    {"role": "system", "content": "You are a helpful assistant fine-tuned for a specific task."},
    {"role": "user", "content": "Generate a response in the style you were trained on."}
]

if not FINE_TUNED_MODEL_ID:
    print("Error: FINE_TUNED_MODEL_NAME environment variable is not set.")
    print("Please set it to your fine-tuned model ID to run this example.")
else:
    print("--- Sending request using SDK ---")
    print(f"Using Fine-Tuned Model: {FINE_TUNED_MODEL_ID}")
    print(f"Messages:
{json.dumps(messages, indent=2)}")
    print("-" * 30)

    try:
        completion = client.chat.completions.create(
            model=FINE_TUNED_MODEL_ID, # Specify the fine-tuned model ID here
            messages=messages,
            max_tokens=100,
            temperature=0.7,
        )

        print("--- Full API Response ---")
        print(completion.model_dump_json(indent=2))
        print("-" * 30)

        # --- Response Handling ---
        assistant_message = completion.choices[0].message.content
        print(f"Assistant Message (from fine-tuned model):")
        print(assistant_message)

    except NotFoundError as e:
        # Specific error for model not found with the SDK
        print(f"API Error: Model not found.")
        print(f"The fine-tuned model ID '{FINE_TUNED_MODEL_ID}' might be incorrect or not available on the endpoint: {API_BASE_URL}")
        print(f"Details: {e}")

    except (APIError, RateLimitError, APITimeoutError) as e:
        print(f"An API error occurred: {e}")
        if hasattr(e, 'status_code'):
            print(f"Status Code: {e.status_code}")
        # ... (rest of standard error handling) ...

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        print(f"Type: {type(e)}")

print("-" * 30)
print("Fine-tuned model SDK example complete.") 