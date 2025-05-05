"""
Example of advanced stream handling with the OpenAI-compatible Chat Completions
endpoint using the 'openai' Python SDK.

This example focuses on processing stream chunks to identify and aggregate
tool calls (functions) as they arrive in the stream.
"""

import os
import json
import sys # Add sys import
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key # Import the synchronous helper

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
# API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key") # Original line
API_KEY = get_api_key() # Fetch key using the helper function
MODEL_NAME = os.getenv("MODEL_NAME") # Optional: If endpoint supports model selection

# --- Initialize OpenAI Client ---
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
print(f"API_KEY: {API_KEY}")
print(f"API_BASE_URL: {API_BASE_URL}")
print(f"MODEL_NAME: {MODEL_NAME}")

# --- Tool Definition (for streaming tool calls) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price for a given ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "The stock ticker symbol, e.g., AAPL",
                    },
                },
                "required": ["ticker"],
            },
        }
    }
]

# --- API Request ---
messages = [{"role": "user", "content": "What is the current price of MSFT?"}]

print("--- Sending streaming request with tools ---")
print(f"Messages: {messages}")
print(f"Tools: {json.dumps(tools, indent=2)}")
print("-" * 30)
print("--- Streaming Response ---")

full_response_content = ""
# Dictionary to aggregate tool call arguments, keyed by index
tool_calls_agg = defaultdict(lambda: {"id": None, "type": "function", "function": {"name": "", "arguments": ""}})

try:
    stream = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools,
        # tool_choice="auto", # Or force a tool: {"type": "function", "function": {"name": "get_stock_price"}}
        tool_choice={"type": "function", "function": {"name": "get_stock_price"}},
        stream=True,
        temperature=0.7,
    )

    for chunk in stream:
        print(f"Raw Chunk: {chunk.model_dump_json(indent=2)}") # Debugging
        if not chunk.choices:
            # Handle potential non-standard chunks or empty choices
            print(f"Received non-standard chunk: {chunk}")
            continue

        choice = chunk.choices[0]
        delta = choice.delta

        # --- Aggregate Content ---
        if delta.content:
            content_piece = delta.content
            print(content_piece, end="", flush=True)
            full_response_content += content_piece

        # --- Aggregate Tool Calls (Newer SDK Structure) ---
        if delta.tool_calls:
            for tool_call_chunk in delta.tool_calls:
                index = tool_call_chunk.index
                tool_id = tool_call_chunk.id
                func_chunk = tool_call_chunk.function

                if tool_id:
                    # First time seeing this tool call index, store its ID
                    tool_calls_agg[index]["id"] = tool_id
                    print(f"\n[Tool Call Start Index:{index} ID:{tool_id}]", end="", flush=True)

                if func_chunk:
                    if func_chunk.name:
                        # Capture the function name
                        tool_calls_agg[index]["function"]["name"] = func_chunk.name
                        print(f" [Name: {func_chunk.name}]", end="", flush=True)
                    if func_chunk.arguments:
                        # Append argument chunks
                        args_piece = func_chunk.arguments
                        tool_calls_agg[index]["function"]["arguments"] += args_piece
                        print(f" [Arg Chunk: {args_piece}]", end="", flush=True)

        # Check for finish reason
        if choice.finish_reason:
             print(f"\n[STREAM FINISHED Reason: {choice.finish_reason}]")

    print("-" * 30) # End of stream output

    # --- Post-Stream Processing ---
    print("--- Aggregated Results ---")
    print(f"Full Text Content:\n{full_response_content}")

    if tool_calls_agg:
        print("\n--- Aggregated Tool Calls ---")
        final_tool_calls = list(tool_calls_agg.values()) # Convert back to list
        for i, tool_call in enumerate(final_tool_calls):
            print(f"\nTool Call {i}:")
            print(f"  ID: {tool_call.get('id')}")
            print(f"  Type: {tool_call.get('type')}")
            function_info = tool_call.get("function", {})
            print(f"  Function Name: {function_info.get('name')}")
            raw_args = function_info.get('arguments', '')
            try:
                # Attempt to parse the fully aggregated arguments string
                final_args = json.loads(raw_args)
                print(f"  Arguments (Parsed):\n{json.dumps(final_args, indent=4)}")
                # Here you would typically execute the function
            except json.JSONDecodeError:
                print(f"  Arguments (Raw/Failed to Parse):\n{raw_args}")
                print("  Could not decode arguments JSON.")
        print("-" * 30)

except (APIError, RateLimitError, APITimeoutError) as e:
    print(f"\n--- OpenAI API Error Occurred ---")
    print(f"Error Type: {type(e)}")
    print(f"Status Code: {e.status_code if hasattr(e, 'status_code') else 'N/A'}")
    print(f"Message: {e}")
    # You can access more details if needed, e.g., e.request, e.body
    # print(f"Request: {e.request}")
    # print(f"Body: {e.body}")
except Exception as e:
    print(f"\n--- An Unexpected Error Occurred ---")
    print(f"Error Type: {type(e)}")
    print(f"Message: {e}")
    # Consider adding traceback for unexpected errors
    import traceback
    traceback.print_exc()

print("Advanced streaming SDK example complete.") 