"""
Example of enforcing structured output using Pydantic models and the
OpenAI-compatible Chat Completions endpoint with the 'openai' Python SDK,
specifically for generating car descriptions.
"""

import os
import sys
from enum import Enum
from dotenv import load_dotenv
from pydantic import BaseModel
from openai import OpenAI

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

# --- Initialize OpenAI Client ---
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

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

    try:
        client.api_key = get_api_key()
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            extra_body={"guided_json": json_schema},
        )

        # --- Response Handling ---
        if completion.choices and completion.choices[0].message and completion.choices[0].message.content:
            print("--- Successfully received structured output ---")
            print("Generated Car Description:")
            print(completion.choices[0].message.content)
        else:
            print("Error: Model did not return the expected data.")
            if completion.choices and completion.choices[0].message:
                print(f"Raw message: {completion.choices[0].message}")


    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 