"""
Example of using the OpenAI-compatible Chat Completions endpoint with the
'temperature' parameter using the 'requests' library.

Demonstrates how to influence the randomness and creativity of the model's output.
"""

import os
import json
import sys
import requests # Added import
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key # Assuming this helper is still used

# Get endpoint from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional: If endpoint supports model selection
CHAT_COMPLETIONS_ENDPOINT = f"{API_BASE_URL}/chat/completions"

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

# --- API Request Function (To be implemented) ---
def generate_completion_with_temperature(prompt_content: str, temp_value: float):
    """Generates a completion for a given prompt and temperature using requests."""
    api_key = get_api_key()
    if not api_key:
        print(f"Error: API key not found. Please set {os.getenv('API_KEY_ENV_VAR', 'OPENAI_API_KEY')} environment variable.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt_content}],
        "temperature": temp_value,
        "max_tokens": 70, # Increased for more varied output
        "n": 1
    }
    # Filter out None model if MODEL_NAME is not set
    if MODEL_NAME is None:
        data.pop("model", None)

    print(f"--- Sending request with Temperature: {temp_value} ---")
    # Use single quotes for the outer f-string to avoid issues with inner double quotes
    print(f'Prompt: "{prompt_content}"')
    print("Target Endpoint:", CHAT_COMPLETIONS_ENDPOINT)
    # print("Payload:", json.dumps(data, indent=2)) # For debugging
    print("-" * 30)

    try:
        response = requests.post(
            CHAT_COMPLETIONS_ENDPOINT,
            headers=headers,
            json=data,
            timeout=30  # Set a timeout for the request
        )

        response.raise_for_status()  # Raise an HTTPError for bad responses (4XX or 5XX)

        completion_data = response.json()

        # print("\nFull response JSON:") # For debugging
        # print(json.dumps(completion_data, indent=2))

        if completion_data.get("choices") and len(completion_data["choices"]) > 0:
            assistant_message = completion_data["choices"][0].get("message", {}).get("content")
            if assistant_message:
                print(f"Assistant (Temp: {temp_value}):")
                print(assistant_message)
            else:
                print(f"Error: Could not extract assistant message (Temp: {temp_value}).")
                print("Response structure might be different than expected.")
        else:
            print(f"Error: No choices found in response (Temp: {temp_value}).")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred with Temperature {temp_value}: {e}")
        print(f"Status Code: {e.response.status_code}")
        try:
            print(f"Response Body: {e.response.text}")
        except Exception:
            print("Could not print response body.")
    except requests.exceptions.RequestException as e:
        print(f"A network or request error occurred with Temperature {temp_value}: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response (Temp: {temp_value}): {e}")
        print(f"Response Text: {response.text if 'response' in locals() else 'No response object'}")
    except KeyError as e:
        print(f"Error accessing key in API response (Temp: {temp_value}): {e}")
        # print(json.dumps(completion_data, indent=2) if 'completion_data' in locals() else "No response data")
    except Exception as e:
        print(f"An unexpected error occurred (Temp: {temp_value}): {e}")
        print(f"Type: {type(e)}")
    finally:
        print("-" * 30)
        print("\n")  # Add a newline for better separation of outputs


# --- Main Execution ---
if __name__ == "__main__":
    user_prompt = "Write a short, imaginative story about a brave squirrel on a quest."

    print("--- Demonstrating Effect of Different Temperatures (using requests) ---")

    # Low temperature (more deterministic, focused)
    generate_completion_with_temperature(user_prompt, temp_value=0.1)

    # Medium temperature (balanced)
    generate_completion_with_temperature(user_prompt, temp_value=0.7)

    # High temperature (more random, creative)
    # Note: some endpoints might cap temperature at 1.0
    generate_completion_with_temperature(user_prompt, temp_value=1.0)
    # generate_completion_with_temperature(user_prompt, temp_value=1.5) # If supported

    print("Temperature sampling example with requests complete.")
    print("Observe how the story changes with different temperature settings.")
    print("Low temperatures should produce more predictable and straightforward narratives.")
    print("High temperatures should lead to more surprising and varied storylines.") 