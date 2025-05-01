"""
Example of using the OpenAI-compatible Chat Completions endpoint with 'logit_bias'
parameter using the official 'openai' Python SDK.

Demonstrates how to influence the likelihood of specific tokens appearing in the response.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional: If endpoint supports model selection

# --- Initialize OpenAI Client ---
# Point the client to the custom endpoint
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)

# --- Logit Bias Setup ---
# Logit bias maps token IDs (integers) to bias values (floats from -100 to 100).
# Positive values increase likelihood, negative values decrease likelihood.
# A bias of 100 effectively guarantees the token, -100 effectively bans it.

# IMPORTANT: You need the actual integer token IDs used by the specific model
#            you are targeting. These IDs vary between tokenizers (e.g., GPT-4,
#            Claude, Llama). Finding these IDs usually requires using the
#            tokenizer associated with the model (like tiktoken for OpenAI models).
#
# Example (Illustrative - Replace with actual token IDs for your model):
# Let's assume we found the token IDs for " red" and " blue" (note potential leading space):
#   " red": 1234
#   " blue": 5678
# Let's also assume the token ID for " green" is 9101

# We want to make " red" more likely and ban " green"
# The SDK expects a dictionary where keys are integer token IDs.
example_logit_bias = {
    # 1234: 5,    # Increase likelihood of " red" (Use actual token ID)
    # 9101: -100  # Ban " green" (Use actual token ID)
    # --- Replace above with actual token IDs for your model --- 
    # Placeholder for demonstration - this won't work without correct IDs
    1598: 10,    # Example: Make token ID 1598 more likely 
    8481: -100,  # Example: Ban token ID 8481
}

# --- API Request ---
messages = [
    {"role": "user", "content": "What is your favorite color? Describe it."}
]

print("--- Sending request to model with Logit Bias ---")
print(f"Messages: {messages}")
print(f"Logit Bias (using placeholder token IDs): {example_logit_bias}")
print("\nNOTE: Logit bias requires using the correct integer TOKEN IDs for the target model.")
print("The example bias values are placeholders and may not affect the output correctly.")
print("You must replace the keys in 'logit_bias' with actual token IDs.")
print("-" * 30)

try:
    completion = client.chat.completions.create(
        model=MODEL_NAME, # Required for SDK
        messages=messages,
        logit_bias=example_logit_bias,
        max_tokens=50,
        temperature=0.7,
    )

    print("--- Full API Response ---")
    # Use model_dump_json for cleaner output of Pydantic models
    print(completion.model_dump_json(indent=2))
    print("-" * 30)

    # --- Response Handling ---
    assistant_message = completion.choices[0].message.content
    print(f"Assistant Message (with bias applied):")
    print(assistant_message)

    # You would observe if the output favors tokens with positive bias
    # and avoids tokens with negative bias (especially -100).

except (APIError, RateLimitError, APITimeoutError) as e:
    print(f"An API error occurred: {e}")
    if hasattr(e, 'status_code'):
        print(f"Status Code: {e.status_code}")
    if hasattr(e, 'response') and e.response is not None:
        try:
            print(f"Response Body: {e.response.text}")
        except Exception:
             print("Could not print response body.")
    elif hasattr(e, 'message'):
        print(f"Error Message: {e.message}")

except KeyError as e:
    print(f"Error accessing expected key in API response: {e}")
    print("Response structure might be different than expected.")
    print(completion.model_dump_json(indent=2) if 'completion' in locals() else "No response object")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
    print(f"Type: {type(e)}")

print("-" * 30)
print("Logit bias example complete.") 