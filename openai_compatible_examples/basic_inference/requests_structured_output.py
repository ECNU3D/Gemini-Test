"""
Example of enforcing structured output using Pydantic models and the
OpenAI-compatible Chat Completions endpoint with the 'requests' Python library,
specifically for generating car descriptions.
"""

import os
import sys
import json
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel
import requests

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.auth_helpers import get_api_key

# --- Configuration ---
load_dotenv()  # Load environment variables from .env file

API_BASE_URL = os.getenv("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-3B-Instruct") # Default model if not set

# --- Pydantic Models ---
class CarType(str, Enum):
    sedan = "sedan"
    suv = "SUV"
    truck = "Truck"
    coupe = "Coupe"

class CarDescription(BaseModel):
    brand: str
    model: str
    car_type: CarType

def main():
    # --- API Request ---
    json_schema = CarDescription.model_json_schema()

    messages = [
        {
            "role": "user",
            "content": "Generate a JSON with the brand, model and car_type of the most iconic car from the 90's",
        }
    ]

    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "guided_json": json_schema
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()  # Raise an exception for bad status codes

        completion = response.json()

        # --- Response Handling ---
        if completion.get("choices") and \
           completion["choices"][0].get("message") and \
           completion["choices"][0]["message"].get("content"):
            print("--- Successfully received structured output ---")
            print("Generated Car Description:")
            # The content is a JSON string, so we parse it for pretty printing or further use
            # For this example, we'll print it as is, assuming it's well-formed JSON.
            print(completion["choices"][0]["message"]["content"])
        else:
            print("Error: Model did not return the expected data.")
            print(f"Raw response: {completion}")

    except requests.exceptions.RequestException as e:
        print(f"An HTTP error occurred: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"Response content: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"Response content: {e.response.text}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 