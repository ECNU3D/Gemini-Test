"""
Example of using the OpenAI-compatible Chat Completions endpoint with
'presence_penalty' and 'frequency_penalty' parameters using the official
'openai' Python SDK.

Demonstrates how to discourage the model from repeating tokens or topics.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional: If endpoint supports model selection

# --- Initialize OpenAI Client ---
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
)

# --- Presence and Frequency Penalty Explanation ---
# These penalties modify the likelihood of tokens appearing based on their presence
# or frequency in the generated text so far.
# Both range from -2.0 to 2.0. Higher positive values increase the penalty.
# Negative values would encourage token repetition (less common use case).

# Presence Penalty:
# - Positive values penalize new tokens based on whether they have appeared in the
#   text so far, increasing the model's likelihood to talk about new topics.
# - A value of 0 means no penalty.
# - Useful for discouraging topic repetition and encouraging more diverse output.

# Frequency Penalty:
# - Positive values penalize new tokens based on their existing frequency in the
#   text so far, decreasing the model's likelihood to repeat the same line verbatim.
# - A value of 0 means no penalty.
# - Useful for reducing word-level repetition, making text less monotonous.

# --- API Request Function ---
def generate_completion_with_penalties(
    prompt_content: str,
    presence_val: float = 0.0,
    frequency_val: float = 0.0,
    temp: float = 0.7 # Keep temperature consistent for comparison
):
    """Generates a completion with specified presence and frequency penalties."""
    messages = [
        {"role": "user", "content": prompt_content}
    ]

    print(f"--- Sending request with Presence Penalty: {presence_val}, Frequency Penalty: {frequency_val}, Temp: {temp} ---")
    print(f'Prompt: "{prompt_content}"')
    print("-" * 30)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temp,
            presence_penalty=presence_val,
            frequency_penalty=frequency_val,
            max_tokens=150, # Allow more tokens to see penalty effects
            n=1
        )

        assistant_message = completion.choices[0].message.content
        print(f"Assistant (PP: {presence_val}, FP: {frequency_val}):")
        print(assistant_message)

    except (APIError, RateLimitError, APITimeoutError) as e:
        print(f"An API error occurred (PP: {presence_val}, FP: {frequency_val}): {e}")
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
        print(f"Error accessing key in API response (PP: {presence_val}, FP: {frequency_val}): {e}")
    except Exception as e:
        print(f"An unexpected error occurred (PP: {presence_val}, FP: {frequency_val}): {e}")
        print(f"Type: {type(e)}")
    finally:
        print("-" * 30)
        print("\n")

# --- Main Execution ---
if __name__ == "__main__":
    # A prompt that might lead to repetition if not controlled
    user_prompt = (
        "Describe the key features of a good fantasy novel. "
        "Elaborate on why these features are important. "
        "Then, discuss some common tropes in fantasy that readers enjoy."
    )

    fixed_temperature = 0.7
    print(f"--- Demonstrating Penalties (Temperature fixed at {fixed_temperature}) ---")

    # 1. No penalties (baseline)
    print("\nRunning with NO penalties (baseline):")
    generate_completion_with_penalties(user_prompt, temp=fixed_temperature, presence_val=0.0, frequency_val=0.0)

    # 2. Only Presence Penalty (e.g., 0.5)
    #    Should encourage discussion of different features/tropes without repeating them.
    print("\nRunning with POSITIVE PRESENCE penalty (e.g., 0.5):")
    generate_completion_with_penalties(user_prompt, temp=fixed_temperature, presence_val=0.5, frequency_val=0.0)

    # 3. Only Frequency Penalty (e.g., 0.5)
    #    Should reduce verbatim repetition of specific words or phrases used to describe features.
    print("\nRunning with POSITIVE FREQUENCY penalty (e.g., 0.5):")
    generate_completion_with_penalties(user_prompt, temp=fixed_temperature, presence_val=0.0, frequency_val=0.5)

    # 4. Both Penalties (e.g., 0.5 each)
    #    Strongest effect on reducing overall repetition and encouraging novelty.
    print("\nRunning with BOTH POSITIVE penalties (e.g., 0.5 each):")
    generate_completion_with_penalties(user_prompt, temp=fixed_temperature, presence_val=0.5, frequency_val=0.5)

    # 5. Higher Penalties (e.g., 1.0 each)
    #    Watch for output becoming too disjointed or avoiding natural phrasing.
    print("\nRunning with HIGHER penalties (e.g., 1.0 each):")
    generate_completion_with_penalties(user_prompt, temp=fixed_temperature, presence_val=1.0, frequency_val=1.0)

    print("Presence and Frequency penalty example complete.")
    print("Observe how the responses change, especially regarding repetition of ideas and phrases,")
    print("when different penalty values are applied.") 