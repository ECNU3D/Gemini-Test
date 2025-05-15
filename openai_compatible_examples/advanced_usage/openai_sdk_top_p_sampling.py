"""
Example of using the OpenAI-compatible Chat Completions endpoint with the
'top_p' (nucleus sampling) parameter using the official 'openai' Python SDK.

Demonstrates how to control the diversity of the model's output by selecting
from the smallest set of tokens whose cumulative probability exceeds top_p.
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
    """Generates a completion for a given prompt, top_p, and a fixed temperature."""
    messages = [
        {"role": "user", "content": prompt_content}
    ]

    print(f"--- Sending request with Top_p: {top_p_value} (Temperature: {current_temperature}) ---")
    print(f'Prompt: "{prompt_content}"')
    print("-" * 30)

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            top_p=top_p_value,
            temperature=current_temperature, # Keep temperature fixed to isolate top_p effect
            max_tokens=70,
            n=1
        )

        assistant_message = completion.choices[0].message.content
        print(f"Assistant (Top_p: {top_p_value}):")
        print(assistant_message)

    except (APIError, RateLimitError, APITimeoutError) as e:
        print(f"An API error occurred with Top_p {top_p_value}: {e}")
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
        print(f"Error accessing key in API response (Top_p: {top_p_value}): {e}")
    except Exception as e:
        print(f"An unexpected error occurred (Top_p: {top_p_value}): {e}")
        print(f"Type: {type(e)}")
    finally:
        print("-" * 30)
        print("\n")

# --- Main Execution ---
if __name__ == "__main__":
    user_prompt = "Tell me a fun fact about the ocean."
    # We'll keep temperature somewhat neutral (e.g., 0.7) to see top_p's effect
    # Or set temperature to 1.0 if you want top_p to be the primary controller of randomness
    fixed_temperature = 0.7

    print(f"--- Demonstrating Effect of Different Top_p Values (Temperature fixed at {fixed_temperature}) ---")

    # Low top_p (more focused, less diverse)
    generate_completion_with_top_p(user_prompt, top_p_value=0.1, current_temperature=fixed_temperature)

    # Medium top_p (balanced)
    generate_completion_with_top_p(user_prompt, top_p_value=0.5, current_temperature=fixed_temperature)

    # High top_p (more diverse, but still constrained by probability mass)
    generate_completion_with_top_p(user_prompt, top_p_value=0.9, current_temperature=fixed_temperature)

    # Top_p = 1.0 (equivalent to only using temperature for sampling control)
    generate_completion_with_top_p(user_prompt, top_p_value=1.0, current_temperature=fixed_temperature)


    print("Top_p sampling example complete.")
    print("Observe how the fun facts change with different top_p settings while temperature is held constant.")
    print("Low top_p values should lead to more common or straightforward facts.")
    print("Higher top_p values might introduce more unusual or varied facts.") 