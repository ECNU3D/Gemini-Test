"""
Example of using the OpenAI-compatible Chat Completions endpoint with the
'top_p' (nucleus sampling) parameter using the 'requests' Python library.

Demonstrates how to control the diversity of the model's output by selecting
from the smallest set of tokens whose cumulative probability exceeds top_p.
"""

import os
import json
import sys
import subprocess
from datetime import datetime, timedelta
import requests # Import requests
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional: If endpoint supports model selection
API_KEY_EXPIRY_MINUTES = 30 # Same as in auth_helpers

# --- API Key Management ---
_api_key_cache = None
_api_key_last_fetch_time = None
_api_key_expiry_duration = timedelta(minutes=API_KEY_EXPIRY_MINUTES)

def get_fresh_api_key():
    """Fetches the access token using gcloud command."""
    try:
        result = subprocess.run(
            "gcloud auth print-access-token",
            capture_output=True,
            text=True,
            check=True,
            shell=True # Using shell=True for compatibility
        )
        key = result.stdout.strip()
        # print("[Auth] Successfully fetched access token using gcloud.") # Optional: for debugging
        return key
    except FileNotFoundError:
        print("[Auth] Error: 'gcloud' command not found. Make sure Google Cloud SDK is installed and in PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[Auth] Error executing gcloud command: {e}")
        print(f"[Auth] Stderr: {e.stderr.strip()}")
        return None
    except Exception as e:
        print(f"[Auth] An unexpected error occurred while fetching gcloud token: {e}")
        return None

def get_api_key():
    """Gets the current (potentially refreshed) API key."""
    global _api_key_cache, _api_key_last_fetch_time

    is_expired = True
    if _api_key_cache and _api_key_last_fetch_time:
        if datetime.now() <= _api_key_last_fetch_time + _api_key_expiry_duration:
            is_expired = False

    if is_expired:
        # print("[Auth] API key expired or not set, refreshing...") # Optional: for debugging
        new_key = get_fresh_api_key()
        if new_key:
            _api_key_cache = new_key
            _api_key_last_fetch_time = datetime.now()
            # print(f"[Auth] Refreshed API key at {_api_key_last_fetch_time.strftime('%Y-%m-%d %H:%M:%S')}") # Optional
        else:
            print("[Auth] Failed to refresh API key. Using potentially stale key or None.")
            # If refresh fails, it will use the old key if available, or None
            # You might want to raise an error here if a key is critical and refresh fails
    
    return _api_key_cache

# --- Top-p (Nucleus Sampling) Explanation ---
# The 'top_p' parameter controls the diversity of the model's output via nucleus sampling.
# It instructs the model to consider only the tokens that make up the top 'p'
# probability mass.
# - A lower top_p (e.g., 0.1) makes the output more focused and deterministic, as the
#   model only considers a small set of the most likely tokens.
# - A higher top_p (e.g., 0.9) allows for more diversity, as the model can sample
#   from a larger set of tokens, including less likely ones.
# - A top_p of 1.0 means the model considers all tokens in the vocabulary (though
#   practically, it's still limited by the model's probability distribution).
#
# Typical range: 0.0 to 1.0.
# Default is often 1.0 if not specified.
#
# When to use which:
# - Low top_p: Useful when you want highly predictable and conservative responses.
# - High top_p: Good for creative tasks where you want more variety but still want
#   to cap the "long tail" of very unlikely tokens, offering a balance between
#   creativity and coherence.
#
# It's often recommended to alter EITHER temperature OR top_p, but not both,
# as they both control the sampling strategy.
# If you use both, the one that is more restrictive will likely dominate.

# --- API Request Function ---
def generate_completion_with_top_p(prompt_content: str, top_p_value: float, current_temperature: float = 0.7):
    """Generates a completion for a given prompt, top_p, and a fixed temperature using requests."""
    
    api_key = get_api_key()
    if not api_key:
        print("Error: Could not retrieve API key. Please check gcloud authentication.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME, # Required if your endpoint needs it
        "messages": [
            {"role": "user", "content": prompt_content}
        ],
        "top_p": top_p_value,
        "temperature": current_temperature,
        "max_tokens": 70,
        "n": 1
    }
    # If MODEL_NAME is not set or empty, remove it from payload as some endpoints might error
    if not MODEL_NAME:
        del payload["model"]

    chat_completions_url = f"{API_BASE_URL.rstrip('/')}/chat/completions"

    print(f"--- Sending request with Top_p: {top_p_value} (Temperature: {current_temperature}) ---")
    print(f'Attempting POST to: {chat_completions_url}')
    print(f'Prompt: "{prompt_content}"')
    print(f'Payload: {json.dumps(payload, indent=2)}') # Log the payload for debugging
    print("-" * 30)

    try:
        response = requests.post(chat_completions_url, headers=headers, json=payload, timeout=30) # Added timeout
        response.raise_for_status()  # Raise an exception for HTTP errors (4XX or 5XX)

        completion_data = response.json()
        
        if completion_data.get("choices") and len(completion_data["choices"]) > 0:
            assistant_message = completion_data["choices"][0].get("message", {}).get("content")
            if assistant_message:
                print(f"Assistant (Top_p: {top_p_value}):")
                print(assistant_message)
            else:
                print(f"Error: 'content' not found in response choice (Top_p: {top_p_value}).")
                print(f"Response JSON: {json.dumps(completion_data, indent=2)}")
        else:
            print(f"Error: 'choices' not found or empty in API response (Top_p: {top_p_value}).")
            print(f"Response JSON: {json.dumps(completion_data, indent=2)}")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred with Top_p {top_p_value}: {e}")
        print(f"Status Code: {e.response.status_code}")
        try:
            print(f"Response Body: {e.response.text}")
        except Exception:
            print("Could not print response body.")
    except requests.exceptions.RequestException as e: # Catch other requests errors like timeout, connection error
        print(f"A requests error occurred with Top_p {top_p_value}: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response (Top_p: {top_p_value}): {e}")
        print(f"Raw response text: {response.text if 'response' in locals() else 'Response not available'}")
    except KeyError as e:
        print(f"Error accessing key in API response (Top_p: {top_p_value}): {e}")
        print(f"Response JSON: {json.dumps(completion_data, indent=2) if 'completion_data' in locals() else 'Completion data not available'}")
    except Exception as e:
        print(f"An unexpected error occurred (Top_p: {top_p_value}): {e}")
        print(f"Type: {type(e)}")
    finally:
        print("-" * 30)
        print("\n")

# --- Main Execution ---
if __name__ == "__main__":
    user_prompt = "Tell me a fun fact about the ocean."
    fixed_temperature = 0.7

    print(f"--- Demonstrating Effect of Different Top_p Values (Temperature fixed at {fixed_temperature}) using 'requests' ---")

    # Low top_p (more focused, less diverse)
    generate_completion_with_top_p(user_prompt, top_p_value=0.1, current_temperature=fixed_temperature)

    # Medium top_p (balanced)
    generate_completion_with_top_p(user_prompt, top_p_value=0.5, current_temperature=fixed_temperature)

    # High top_p (more diverse, but still constrained by probability mass)
    generate_completion_with_top_p(user_prompt, top_p_value=0.9, current_temperature=fixed_temperature)

    # Top_p = 1.0 (equivalent to only using temperature for sampling control)
    generate_completion_with_top_p(user_prompt, top_p_value=1.0, current_temperature=fixed_temperature)

    print("Top_p sampling example with 'requests' complete.")
    print("Observe how the fun facts change with different top_p settings while temperature is held constant.")
    print("Low top_p values should lead to more common or straightforward facts.")
    print("Higher top_p values might introduce more unusual or varied facts.") 