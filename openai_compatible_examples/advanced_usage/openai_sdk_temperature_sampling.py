"""
Example of using the OpenAI-compatible Chat Completions endpoint with the
'temperature' parameter using the official 'openai' Python SDK.

Demonstrates how to influence the randomness and creativity of the model's output.
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

# --- Temperature Explanation ---
# The 'temperature' parameter controls the randomness of the model's output.
# - A lower temperature (e.g., 0.0 - 0.3) makes the output more deterministic,
#   focused, and conservative. The model is more likely to choose the highest
#   probability words.
# - A higher temperature (e.g., 0.7 - 1.0, or higher if supported) makes the
#   output more random, creative, and diverse. It allows the model to explore
#   less likely options.
#
# Typical range: 0.0 to 1.0 (some models/endpoints might support up to 2.0).
#
# When to use which:
# - Low temperature: Good for factual Q&A, code generation, summarization
#   where precision and conciseness are important.
# - High temperature: Good for creative writing, brainstorming, generating
#   multiple diverse options.
#
# It's often recommended to alter EITHER temperature OR top_p, but not both,
# as they both control the sampling strategy.

# --- API Request Function ---
def generate_completion_with_temperature(prompt_content: str, temp_value: float):
    """Generates a completion for a given prompt and temperature."""
    messages = [
        {"role": "user", "content": prompt_content}
    ]

    print(f"--- Sending request with Temperature: {temp_value} ---")
    # Use single quotes for the outer f-string to avoid issues with inner double quotes
    print(f'Prompt: "{prompt_content}"')
    print("-" * 30)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp_value,
            max_tokens=70, # Increased for more varied output
            n=1 # We'll make separate calls to see distinct temperature effects
        )

        assistant_message = completion.choices[0].message.content
        print(f"Assistant (Temp: {temp_value}):")
        print(assistant_message)
        # print("\nFull response object:")
        # print(completion.model_dump_json(indent=2))

    except (APIError, RateLimitError, APITimeoutError) as e:
        print(f"An API error occurred with Temperature {temp_value}: {e}")
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
        print(f"Error accessing key in API response (Temp: {temp_value}): {e}")
        # print(completion.model_dump_json(indent=2) if 'completion' in locals() else "No response object")
    except Exception as e:
        print(f"An unexpected error occurred (Temp: {temp_value}): {e}")
        print(f"Type: {type(e)}")
    finally:
        print("-" * 30)
        print("\n") # Add a newline for better separation of outputs


# --- Main Execution ---
if __name__ == "__main__":
    user_prompt = "Write a short, imaginative story about a brave squirrel on a quest."

    print("--- Demonstrating Effect of Different Temperatures ---")

    # Low temperature (more deterministic, focused)
    generate_completion_with_temperature(user_prompt, temp_value=0.1)

    # Medium temperature (balanced)
    generate_completion_with_temperature(user_prompt, temp_value=0.7)

    # High temperature (more random, creative)
    # Note: some endpoints might cap temperature at 1.0
    generate_completion_with_temperature(user_prompt, temp_value=1.0)
    # generate_completion_with_temperature(user_prompt, temp_value=1.5) # If supported

    print("Temperature sampling example complete.")
    print("Observe how the story changes with different temperature settings.")
    print("Low temperatures should produce more predictable and straightforward narratives.")
    print("High temperatures should lead to more surprising and varied storylines.") 