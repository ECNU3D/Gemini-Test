"""
Example of using the OpenAI-compatible Chat Completions endpoint with 'functions'
parameter using the 'requests' library.

Demonstrates how the model can identify when to use a function and how to
parse the response.
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

# --- Function Definition ---
# Define the function(s) we want the model to be able to call
# See: https://platform.openai.com/docs/guides/function-calling

functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }
]

# --- API Request ---
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

# Example conversation where a function call is likely needed
messages = [{"role": "user", "content": "What's the weather like in Boston?"}]

payload = {
    "model": MODEL_NAME, # Include if required by your endpoint
    "messages": messages,
    "functions": functions,
    "function_call": "auto",  # Let the model decide whether to call a function
}

# Remove None values from payload (like model if not set)
payload = {k: v for k, v in payload.items() if v is not None}

print(f"--- Sending request to: {CHAT_COMPLETIONS_URL} ---")
print(f"Payload:
{json.dumps(payload, indent=2)}")
print("-" * 30)

try:
    response = requests.post(CHAT_COMPLETIONS_URL, headers=headers, json=payload)
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

    response_data = response.json()
    print(f"--- Full API Response ---")
    print(json.dumps(response_data, indent=2))
    print("-" * 30)

    # --- Response Handling ---
    response_message = response_data["choices"][0]["message"]

    # Check if the model wants to call a function
    if response_message.get("function_call"):
        function_call_info = response_message["function_call"]
        function_name = function_call_info["name"]
        function_args_str = function_call_info["arguments"]
        function_args = json.loads(function_args_str) # Arguments are often a JSON string

        print(f"--- Model requested function call ---")
        print(f"Function Name: {function_name}")
        print(f"Arguments:
{json.dumps(function_args, indent=2)}")
        print("-" * 30)

        # --- (Simulated) Function Execution ---
        # Here you would actually execute your function based on the name and args
        if function_name == "get_current_weather":
            location = function_args.get("location")
            unit = function_args.get("unit", "fahrenheit") # Default unit
            # In a real app, call your weather API here
            function_response_content = json.dumps(
                {"location": location, "temperature": "72", "unit": unit}
            )
            print(f"--- (Simulated) Executing function: {function_name} ---")
            print(f"Result: {function_response_content}")
            print("-" * 30)

            # --- Sending Function Result Back to Model ---
            # Append the original response message and the function result
            messages.append(response_message) # Add assistant's function call message
            messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response_content,
                }
            )

            # Update payload for the second call
            follow_up_payload = {
                "model": MODEL_NAME,
                "messages": messages,
                # Don't need 'functions' or 'function_call' usually for the second call
            }
            follow_up_payload = {k: v for k, v in follow_up_payload.items() if v is not None}

            print(f"--- Sending function result back to model ---")
            print(f"Payload:
{json.dumps(follow_up_payload, indent=2)}")
            print("-" * 30)

            follow_up_response = requests.post(
                CHAT_COMPLETIONS_URL, headers=headers, json=follow_up_payload
            )
            follow_up_response.raise_for_status()
            follow_up_data = follow_up_response.json()

            print(f"--- Final API Response ---")
            print(json.dumps(follow_up_data, indent=2))
            print("-" * 30)

            final_message = follow_up_data["choices"][0]["message"]["content"]
            print(f"Final Assistant Message:
{final_message}")

        else:
            print(f"Error: Model requested unknown function '{function_name}'")

    else:
        # The model generated a normal text response
        final_message = response_message["content"]
        print(f"--- Model generated text response directly ---")
        print(f"Assistant Message:
{final_message}")


except requests.exceptions.RequestException as e:
    print(f"An API error occurred: {e}")
    if e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        try:
            print(f"Response Body: {e.response.text}")
        except Exception:
            print("Could not print response body.")

except json.JSONDecodeError as e:
    print(f"Error decoding JSON from function arguments or API response: {e}")
    print(f"Problematic string: {function_args_str if 'function_args_str' in locals() else 'API Response'}")

except KeyError as e:
    print(f"Error accessing expected key in API response: {e}")
    print("Response structure might be different than expected.")

except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("-" * 30)
print("Function calling example complete.") 