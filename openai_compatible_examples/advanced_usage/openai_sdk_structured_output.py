"""
Example of enforcing structured output using forced tool calling with the
OpenAI-compatible Chat Completions endpoint and the 'openai' Python SDK.

By defining a tool and forcing the model to use it (`tool_choice`),
we compel the output to match the tool's parameter schema.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional

# --- Initialize OpenAI Client ---
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# --- Tool Definition (Desired Output Schema) ---
# Define a tool whose parameters match the desired structured output.
tools = [
    {
        "type": "function",
        "function": {
            "name": "extract_event_details",
            "description": "Extracts event details from the provided text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_name": {
                        "type": "string",
                        "description": "The name or title of the event.",
                    },
                    "date": {
                        "type": "string",
                        "description": "The date of the event (e.g., YYYY-MM-DD).",
                    },
                    "location": {
                        "type": "string",
                        "description": "The location or venue of the event.",
                    },
                },
                "required": ["event_name", "date"], # Specify required fields
            },
        }
    }
]

# --- API Request ---
# Input text containing information to be extracted
input_text = "The annual tech conference is happening on 2024-10-26 at the downtown convention center."
messages = [
    {"role": "system", "content": "You are an expert data extraction assistant."},
    {"role": "user", "content": f"Extract event details from this text: {input_text}"}
]

# Force the model to use the specified tool
forced_tool_choice = {"type": "function", "function": {"name": "extract_event_details"}}

print("--- Sending request to force structured output via tool call (SDK) ---")
print(f"Target Tool: {forced_tool_choice['function']['name']}")
print(f"Payload Structure:
{json.dumps({'model': MODEL_NAME, 'messages': messages, 'tools': tools, 'tool_choice': forced_tool_choice}, indent=2)}")
print("-" * 30)

try:
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice=forced_tool_choice, # Force calling this specific tool
    )

    print("--- Full API Response ---")
    print(completion.model_dump_json(indent=2))
    print("-" * 30)

    # --- Response Handling ---
    response_message = completion.choices[0].message

    if response_message.tool_calls:
        tool_call = response_message.tool_calls[0] # Expecting only one forced call
        function_name = tool_call.function.name
        function_args_str = tool_call.function.arguments

        if function_name == "extract_event_details":
            print(f"--- Successfully received structured output via tool call ---")
            try:
                structured_output = json.loads(function_args_str)
                print(f"Extracted Data (JSON):
{json.dumps(structured_output, indent=2)}")
                # Now you can directly use the structured_output dictionary
                print(f"\nAccessing fields:")
                print(f"  Event: {structured_output.get('event_name')}")
                print(f"  Date: {structured_output.get('date')}")
                print(f"  Location: {structured_output.get('location')}") # Might be None if not required/found
            except json.JSONDecodeError:
                print("Error: Could not decode tool arguments JSON.")
                print(f"Raw Arguments: {function_args_str}")
        else:
            print("Error: Response did not contain the expected tool call.")
            print(f"Received: {tool_call}")
    else:
        # This shouldn't happen if tool_choice was forced correctly
        print("Error: Model did not return a tool call as expected.")
        print(f"Assistant Message: {response_message.content}")

except (APIError, RateLimitError, APITimeoutError) as e:
    print(f"An API error occurred: {e}")
    # ... (rest of error handling) ...
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    print(f"Type: {type(e)}")

print("-" * 30)
print("Structured output (SDK) example complete.") 