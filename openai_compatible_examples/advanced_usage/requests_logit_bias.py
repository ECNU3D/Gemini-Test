"""
Example of using the OpenAI-compatible Chat Completions endpoint with 'logit_bias'
parameter using the 'requests' library.

Demonstrates how to influence the likelihood of specific tokens appearing in the response.
"""

import os
import json
import requests
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional: If endpoint supports model selection

CHAT_COMPLETIONS_URL = f"{API_BASE_URL}/chat/completions"

# --- Logit Bias Setup ---
# Logit bias maps token IDs (integers) to bias values (floats from -100 to 100).
# Positive values increase likelihood, negative values decrease likelihood.
# A bias of 100 effectively guarantees the token, -100 effectively bans it.

# IMPORTANT: You need the actual integer token IDs used by the specific model
#            you are targeting. These IDs vary between tokenizers (e.g., GPT-4,
#            Claude, Llama). Finding these IDs usually requires using the
#            tokenizer associated with the model.
#
# Example (Illustrative - Replace with actual token IDs for your model):
# Let's assume we found the token IDs for " red" and " blue" (note potential leading space):
#   " red": 1234
#   " blue": 5678
# Let's also assume the token ID for " green" is 9101

# We want to make " red" more likely and ban " green"
example_logit_bias = {
    # "1234": 5,    # Increase likelihood of " red" (Use actual token ID)
    # "9101": -100  # Ban " green" (Use actual token ID)
    # --- Replace above with actual token IDs for your model --- 
    # Placeholder for demonstration - this won't work without correct IDs
    "1598": 10,    # Example: Make token ID 1598 more likely 
    "8481": -100,  # Example: Ban token ID 8481
}

# Note: The API expects keys to be strings, even though they represent integer IDs.

# --- API Request ---
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

messages = [
    {"role": "user", "content": "What is your favorite color? Describe it."}
]

payload = {
    "model": MODEL_NAME, # Include if required by your endpoint
    "messages": messages,
    "logit_bias": example_logit_bias,
    "max_tokens": 50,
    "temperature": 0.7,
}

# Remove None values from payload (like model if not set)
payload = {k: v for k, v in payload.items() if v is not None}

print(f"--- Sending request to: {CHAT_COMPLETIONS_URL} ---")
print(f"Payload with Logit Bias:
{json.dumps(payload, indent=2)}")
print("\nNOTE: Logit bias requires using the correct integer TOKEN IDs for the target model.")
print("The example bias values are placeholders and may not affect the output correctly.")
print("You must replace the keys in 'logit_bias' with actual token IDs.")
print("-" * 30)

try:
    response = requests.post(CHAT_COMPLETIONS_URL, headers=headers, json=payload)
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

    response_data = response.json()
    print(f"--- Full API Response ---")
    print(json.dumps(response_data, indent=2))
    print("-" * 30)

    # --- Response Handling ---
    if response_data.get("choices"):
        assistant_message = response_data["choices"][0]["message"]["content"]
        print(f"Assistant Message (with bias applied):")
        print(assistant_message)

        # You would observe if the output favors tokens with positive bias
        # and avoids tokens with negative bias (especially -100).
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

except KeyError as e:
    print(f"Error accessing expected key in API response: {e}")
    print("Response structure might be different than expected.")
    print(json.dumps(response_data if 'response_data' in locals() else {}, indent=2))

except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("-" * 30)
print("Logit bias example complete.") 