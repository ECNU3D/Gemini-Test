"""
Example of advanced stream handling with the OpenAI-compatible Chat Completions
endpoint using the 'requests' library.

This example focuses on processing stream chunks to potentially identify
and aggregate structured data like function/tool calls as they arrive.
"""

import os
import json
import requests
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME") # Optional: If endpoint supports model selection

CHAT_COMPLETIONS_URL = f"{API_BASE_URL}/chat/completions"

# --- Function/Tool Definition (for streaming tool calls) ---
# Define a function the model might call in the stream
functions = [
    {
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
]

# --- API Request ---
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "text/event-stream", # Necessary for SSE
}

# Example conversation prompting a function call
messages = [{"role": "user", "content": "What is the current price of GOOG?"}]

payload = {
    "model": MODEL_NAME,
    "messages": messages,
    "functions": functions,       # Include functions for the model to potentially call
    "function_call": "auto",    # Let the model decide (or force with {"name": "..."})
    "stream": True,             # Enable streaming
    "temperature": 0.7,
}
payload = {k: v for k, v in payload.items() if v is not None} # Clean payload

print(f"--- Sending streaming request to: {CHAT_COMPLETIONS_URL} ---")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("-" * 30)
print("--- Streaming Response ---")

full_response_content = ""
current_function_call = None
function_args_buffer = ""

try:
    with requests.post(CHAT_COMPLETIONS_URL, headers=headers, json=payload, stream=True) as response:
        response.raise_for_status() # Check for HTTP errors

        if "text/event-stream" not in response.headers.get("Content-Type", ""):
            print("Warning: Response Content-Type is not text/event-stream.")
            print(f"Full Response Text:
{response.text}")
            # Fallback or error handling here if needed

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                # print(f"Raw line: {decoded_line}") # Debugging

                if decoded_line.startswith('data:'):
                    data_content = decoded_line[len('data: '):].strip()

                    if data_content == "[DONE]":
                        print("
[STREAM FINISHED]")
                        break # End of stream signal

                    try:
                        chunk = json.loads(data_content)
                        # print(f"Parsed Chunk: {json.dumps(chunk, indent=2)}") # Debugging

                        if not chunk.get("choices"):
                            # Handle potential non-standard chunks or errors in stream
                            print(f"Received non-standard chunk: {chunk}")
                            continue

                        delta = chunk["choices"][0].get("delta", {})

                        # --- Aggregate Content ---
                        if "content" in delta and delta["content"] is not None:
                            content_piece = delta["content"]
                            print(content_piece, end="", flush=True)
                            full_response_content += content_piece

                        # --- Aggregate Function/Tool Calls ---
                        # Note: OpenAI API v1 sends function call info slightly differently
                        # in streams compared to non-streaming. It might arrive in pieces.
                        if "function_call" in delta:
                            func_call_chunk = delta["function_call"]

                            if current_function_call is None:
                                # Start of a function call - capture name if present
                                current_function_call = {"name": func_call_chunk.get("name")}
                                function_args_buffer = "" # Reset buffer for args
                                print(f"
[Function Call Start: {current_function_call['name']}]", end="", flush=True)

                            if "arguments" in func_call_chunk:
                                # Append argument chunks as they arrive
                                args_piece = func_call_chunk["arguments"]
                                function_args_buffer += args_piece
                                print(f" [Arg Chunk: {args_piece}]", end="", flush=True) # Show arrival

                    except json.JSONDecodeError:
                        print(f"
Error decoding JSON chunk: {data_content}")
                    except KeyError as e:
                        print(f"
Error processing chunk structure (KeyError: {e}): {chunk}")
                    except Exception as e:
                        print(f"
Error processing stream chunk: {e}")

        print("-" * 30) # End of stream output

        # --- Post-Stream Processing ---
        print("--- Aggregated Results ---")
        print(f"Full Text Content:
{full_response_content}")

        if current_function_call:
            print("
--- Aggregated Function Call ---")
            print(f"Function Name: {current_function_call.get('name')}")
            try:
                # Attempt to parse the fully aggregated arguments string
                final_args = json.loads(function_args_buffer)
                print(f"Arguments (Parsed):
{json.dumps(final_args, indent=2)}")
                # Here you would typically execute the function based on final_args
            except json.JSONDecodeError:
                print(f"Arguments (Raw/Failed to Parse):
{function_args_buffer}")
                print("Could not decode arguments JSON.")
            print("-" * 30)

except requests.exceptions.RequestException as e:
    print(f"
An API error occurred: {e}")
    if e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        try:
            print(f"Response Body: {e.response.text}")
        except Exception:
            print("Could not print response body.")
except Exception as e:
    print(f"
An unexpected error occurred: {e}")

print("Advanced streaming example complete.") 