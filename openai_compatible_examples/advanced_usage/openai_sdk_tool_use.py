"""
Example of using the OpenAI-compatible Chat Completions endpoint with the
newer 'tools' and 'tool_choice' parameters using the official 'openai' Python SDK.

Demonstrates how the model can identify when to use a tool (function) and how
to parse the response.
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

# --- Tool Definition ---
# Define the tool(s) we want the model to be able to call
# This uses the newer 'tools' format compared to the older 'functions'
# See: https://platform.openai.com/docs/guides/function-calling

tools = [
    {
        "type": "function",
        "function": {
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
    }
]

# --- API Request ---
# Example conversation where a tool call is likely needed
messages = [{"role": "user", "content": "What is the weather like in London?"}]

print("--- Sending initial request to model ---")
print(f"Messages: {messages}")
print(f"Tools: {json.dumps(tools, indent=2)}")
print("-" * 30)

try:
    completion = client.chat.completions.create(
        model=MODEL_NAME, # Required for SDK, even if None/empty for some endpoints
        messages=messages,
        tools=tools,
        tool_choice="auto",  # Let the model decide. Use {"type": "function", "function": {"name": "my_function"}} to force a specific tool
        temperature=0.7,
    )

    print("--- Full API Response (Initial) ---")
    # Use model_dump_json for cleaner output of Pydantic models
    print(completion.model_dump_json(indent=2))
    print("-" * 30)

    response_message = completion.choices[0].message

    # --- Response Handling ---
    tool_calls = response_message.tool_calls

    # Check if the model decided to use a tool
    if tool_calls:
        print("--- Model requested tool call(s) ---")
        # Extend conversation history with the assistant's response (including tool calls)
        messages.append(response_message)

        # --- (Simulated) Tool Execution ---
        # In a real app, you might have multiple tool calls to handle
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args_str = tool_call.function.arguments
            function_args = json.loads(function_args_str)

            print(f"Tool Call ID: {tool_call.id}")
            print(f"Function Name: {function_name}")
            print(f"Arguments:
{json.dumps(function_args, indent=2)}")

            if function_name == "get_current_weather":
                location = function_args.get("location")
                unit = function_args.get("unit", "celsius") # Default unit
                # In a real app, call your weather API here
                function_response_content = json.dumps(
                    {"location": location, "temperature": "15", "unit": unit}
                )
                print(f"--- (Simulated) Executing tool: {function_name} ---")
                print(f"Result: {function_response_content}")
                print("-" * 30)

                # Append the tool result to the conversation history
                messages.append(
                    {
                        "tool_call_id": tool_call.id, # Link the result to the specific call
                        "role": "tool",
                        "name": function_name,
                        "content": function_response_content,
                    }
                )
            else:
                print(f"Error: Model requested unknown tool '{function_name}'")
                # Optionally append an error message for the model
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"error": f"Tool '{function_name}' not found."}),
                    }
                )

        # --- Sending Tool Results Back to Model ---
        print("--- Sending tool results back to model ---")
        print(f"Updated Messages: {json.dumps(messages, indent=2)}")
        print("-" * 30)

        follow_up_completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            # No tools needed usually for the follow-up, model should generate text
        )

        print("--- Final API Response ---")
        print(follow_up_completion.model_dump_json(indent=2))
        print("-" * 30)

        final_message = follow_up_completion.choices[0].message.content
        print(f"Final Assistant Message:
{final_message}")

    else:
        # The model generated a normal text response directly
        final_message = response_message.content
        print("--- Model generated text response directly ---")
        print(f"Assistant Message:
{final_message}")


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

except json.JSONDecodeError as e:
    print(f"Error decoding JSON from function arguments: {e}")
    # Accessing the problematic string might be harder with the SDK structure

except KeyError as e:
    print(f"Error accessing expected key in API response: {e}")
    print("Response structure might be different than expected.")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
    print(f"Type: {type(e)}")

print("-" * 30)
print("Tool use example complete.") 