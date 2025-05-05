"""
Example of using the OpenAI-compatible Chat Completions endpoint with 'functions'
parameter using the 'requests' library.

Demonstrates how the model can identify when to use a function and how to
parse the response.
"""

import os
import json
import requests
import sys
from dotenv import load_dotenv

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key # Use async version

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Get endpoint and API key from environment variables
API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = get_api_key()
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

def main():
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
    print(f"Payload: \
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

        # Check if the model wants to call a function/tool
        tool_calls = response_message.get("tool_calls")
        if tool_calls:
            # For this example, we only handle the first tool call.
            # In a real application, you might need to handle multiple tool calls.
            tool_call = tool_calls[0]
            if tool_call["type"] == "function":
                function_call_info = tool_call["function"]
                function_name = function_call_info["name"]
                # Arguments are a JSON string, need to parse it
                try:
                    function_args_str = function_call_info["arguments"]
                    function_args = json.loads(function_args_str)
                except json.JSONDecodeError as e:
                     print(f"Error decoding JSON from function arguments: {e}")
                     print(f"Problematic string: {function_args_str}")
                     # Handle error appropriately, maybe skip this tool call
                     # or raise an exception depending on requirements.
                     # For this example, we'll re-raise to stop execution here.
                     raise
                except KeyError as e:
                    print(f"Error accessing 'arguments' key in tool call function: {e}")
                    print(f"Tool call info: {function_call_info}")
                    raise # Re-raise to indicate a problem with the response structure


                print(f"--- Model requested function call ---")
                print(f"Function Name: {function_name}")
                print(f"Arguments: \
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
                    # Append the original response message (with tool_calls)
                    # and the tool result message
                    messages.append(response_message) # Add assistant's tool call message
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call["id"], # Use the id from the tool call
                            "name": function_name,
                            "content": function_response_content,
                        }
                    )

                    # Update payload for the second call
                    follow_up_payload = {
                        "model": MODEL_NAME,
                        "messages": messages,
                        # Don't need 'functions' or 'function_call' for the follow-up
                    }
                    follow_up_payload = {k: v for k, v in follow_up_payload.items() if v is not None}

                    print(f"--- Sending function result back to model ---")
                    print(f"Payload: \
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

                    # Extract the final message content correctly
                    final_response_message = follow_up_data["choices"][0]["message"]
                    final_message = final_response_message.get("content", "[No content found in final response]")
                    print(f"Final Assistant Message: \
{final_message}")

                else:
                    print(f"Error: Model requested unknown function '{function_name}'")
                    # Optionally send an error message back to the model
                    # messages.append(response_message)
                    # messages.append({"role": "tool", "tool_call_id": tool_call["id"], "name": function_name, "content": json.dumps({"error": "Unknown function"})})
                    # ... make follow-up call ...

            else:
                 print(f"Error: Received unexpected tool type '{tool_call['type']}'")

        elif response_message.get("content") is not None:
            # The model generated a normal text response
            final_message = response_message["content"]
            print(f"--- Model generated text response directly ---")
            print(f"Assistant Message: \
{final_message}")
        else:
            # Handle cases where the response message structure is unexpected
            # (e.g., neither tool_calls nor content is present)
            print(f"--- Unexpected response message structure ---")
            print(json.dumps(response_message, indent=2))
            print("Could not find 'tool_calls' or 'content' in the message.")


    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")
        if e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            try:
                print(f"Response Body: {e.response.text}")
            except Exception:
                print("Could not print response body.")
        raise

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from function arguments or API response: {e}")
        # Ensure function_args_str exists before trying to print it
        problem_str = "API Response"
        if 'function_args_str' in locals():
            problem_str = function_args_str
        print(f"Problematic string: {problem_str}")
        raise

    except KeyError as e:
        print(f"Error accessing expected key in API response: {e}")
        print("Response structure might be different than expected.")
        # Optionally print the problematic part of the response if available
        if 'response_data' in locals():
            print(f"Response Data causing error: \
{json.dumps(response_data, indent=2)}")
        elif 'follow_up_data' in locals():
            print(f"Follow-up Data causing error: \
{json.dumps(follow_up_data, indent=2)}")
        raise

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

    print("-" * 30)
    print("Function calling example complete.")

if __name__ == "__main__":
    main() 