"""
Example of enforcing structured output using forced function calling with the
OpenAI-compatible Chat Completions endpoint and the 'requests' library.

By defining a function and forcing the model to call it (`function_call`),
we compel the output to match the function's parameter schema.
"""

import os
import json
import requests
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional

CHAT_COMPLETIONS_URL = f"{API_BASE_URL}/chat/completions"

# --- Function Definition (Desired Output Schema) ---
# Define a function whose parameters match the desired structured output.
output_schema_function = [
    {
        "name": "extract_user_info",
        "description": "Extracts user information from the provided text.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The full name of the user.",
                },
                "email": {
                    "type": "string",
                    "description": "The email address of the user.",
                },
                 "age": {
                    "type": "integer",
                    "description": "The age of the user.",
                },
            },
            "required": ["name", "email", "age"], # Specify required fields
        },
    }
]

# --- API Request ---
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

# Input text containing information to be extracted
input_text = "John Doe is 30 years old and his email is john.doe@example.com."
messages = [
    {"role": "system", "content": "You are an expert data extraction assistant."},
    {"role": "user", "content": f"Extract user details from this text: {input_text}"}
]

payload = {
    "model": MODEL_NAME,
    "messages": messages,
    "functions": output_schema_function,
    "function_call": {"name": "extract_user_info"}, # Force calling this specific function
}
payload = {k: v for k, v in payload.items() if v is not None} # Clean payload

print(f"--- Sending request to force structured output via function call ---")
print(f"Target Function: {payload['function_call']['name']}")
print(f"Payload:
{json.dumps(payload, indent=2)}")
print("-" * 30)

try:
    response = requests.post(CHAT_COMPLETIONS_URL, headers=headers, json=payload)
    response.raise_for_status()

    response_data = response.json()
    print(f"--- Full API Response ---")
    print(json.dumps(response_data, indent=2))
    print("-" * 30)

    # --- Response Handling ---
    if response_data.get("choices"):
        response_message = response_data["choices"][0]["message"]

        if response_message.get("function_call"):
            function_call_info = response_message["function_call"]
            function_name = function_call_info.get("name")
            function_args_str = function_call_info.get("arguments")

            if function_name == "extract_user_info" and function_args_str:
                print(f"--- Successfully received structured output via function call ---")
                try:
                    structured_output = json.loads(function_args_str)
                    print(f"Extracted Data (JSON):
{json.dumps(structured_output, indent=2)}")
                    # Now you can directly use the structured_output dictionary
                    print(f"\nAccessing fields:")
                    print(f"  Name: {structured_output.get('name')}")
                    print(f"  Email: {structured_output.get('email')}")
                    print(f"  Age: {structured_output.get('age')}")
                except json.JSONDecodeError:
                    print("Error: Could not decode function arguments JSON.")
                    print(f"Raw Arguments: {function_args_str}")
            else:
                print("Error: Response did not contain the expected function call or arguments.")
                print(f"Received: {response_message}")
        else:
            # This shouldn't happen if function_call was forced correctly
            print("Error: Model did not return a function call as expected.")
            print(f"Assistant Message: {response_message.get('content')}")
    else:
        print("No 'choices' found in the response.")

except requests.exceptions.RequestException as e:
    print(f"An API error occurred: {e}")
    # ... (rest of error handling) ...
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("-" * 30)
print("Structured output (requests) example complete.") 