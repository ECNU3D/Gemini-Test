"""
Example of enforcing structured output using forced tool calling with the
OpenAI-compatible Chat Completions endpoint and the Python requests library.

This example demonstrates how to enforce a complex class structure with various data types.
"""

import os
import json
import requests
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()  # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME")  # Optional

# --- Tool Definition (Complex Class Schema) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "extract_person_details",
            "description": "Extracts person details from the provided text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Full name of the person"
                    },
                    "age": {
                        "type": "integer",
                        "description": "Age in years"
                    },
                    "height": {
                        "type": "number",
                        "description": "Height in meters"
                    },
                    "is_student": {
                        "type": "boolean",
                        "description": "Whether the person is a student"
                    },
                    "hobbies": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of hobbies"
                    },
                    "address": {
                        "type": "object",
                        "properties": {
                            "street": {"type": "string"},
                            "city": {"type": "string"},
                            "zip_code": {"type": "string"}
                        },
                        "required": ["street", "city"]
                    },
                    "scores": {
                        "type": "array",
                        "items": {
                            "type": "number"
                        },
                        "description": "List of test scores"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata about the person"
                    }
                },
                "required": ["name", "age", "is_student"]
            }
        }
    }
]

def main():
    # --- API Request ---
    input_text = """
    John Smith is a 25-year-old student who lives at 123 Main Street, New York, NY 10001. 
    He is 1.85 meters tall and enjoys playing basketball, reading, and coding. 
    His recent test scores were 85.5, 92.0, and 88.5. 
    He has been a student for 3 years and is currently pursuing a degree in Computer Science.
    """
    
    messages = [
        {"role": "system", "content": "You are an expert data extraction assistant."},
        {"role": "user", "content": f"Extract person details from this text: {input_text}"}
    ]

    # Force the model to use the specified tool
    forced_tool_choice = {"type": "function", "function": {"name": "extract_person_details"}}

    # Prepare the request payload
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "tools": tools,
        "tool_choice": forced_tool_choice
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        # Make the API request
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()  # Raise an exception for bad status codes

        # Parse the response
        result = response.json()
        
        # Extract the tool call from the response
        message = result["choices"][0]["message"]
        
        if "tool_calls" in message:
            tool_call = message["tool_calls"][0]
            function_name = tool_call["function"]["name"]
            function_args_str = tool_call["function"]["arguments"]

            if function_name == "extract_person_details":
                print("--- Successfully received structured output ---")
                try:
                    structured_output = json.loads(function_args_str)
                    print(f"Extracted Data (JSON):\n{json.dumps(structured_output, indent=2)}")
                    
                    # Demonstrate accessing the structured data
                    print("\nAccessing fields:")
                    print(f"Name: {structured_output.get('name')}")
                    print(f"Age: {structured_output.get('age')}")
                    print(f"Height: {structured_output.get('height')}")
                    print(f"Is Student: {structured_output.get('is_student')}")
                    print(f"Hobbies: {', '.join(structured_output.get('hobbies', []))}")
                    print(f"Address: {structured_output.get('address', {})}")
                    print(f"Test Scores: {structured_output.get('scores', [])}")
                except json.JSONDecodeError:
                    print("Error: Could not decode tool arguments JSON.")
                    print(f"Raw Arguments: {function_args_str}")
            else:
                print("Error: Response did not contain the expected tool call.")
        else:
            print("Error: Model did not return a tool call as expected.")

    except requests.exceptions.RequestException as e:
        print(f"An API error occurred: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 