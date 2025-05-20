"""
Example of enforcing structured output using Pydantic models and automatic parsing with the
OpenAI-compatible Chat Completions endpoint and the 'openai' Python SDK.

This example demonstrates how to enforce a complex class structure with various data types.
"""

import os
import sys
from typing import List, Optional
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
MODEL_NAME = os.getenv("MODEL_NAME")  # Optional

# --- Initialize OpenAI Client ---
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

# --- Pydantic Models ---
class Address(BaseModel):
    street: str
    city: str
    zip_code: Optional[str] = None

class PersonDetails(BaseModel):
    name: str
    age: int
    height: Optional[float] = None
    is_student: bool
    hobbies: Optional[List[str]] = None
    address: Optional[Address] = None
    scores: Optional[List[float]] = None
    metadata: Optional[dict] = None

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

    try:
        client.api_key = get_api_key()
        completion = client.beta.chat.completions.parse(
            model=MODEL_NAME,
            messages=messages,
            response_format=PersonDetails,
            extra_body=dict(guided_decoding_backend="outlines")
        )

        # --- Response Handling ---
        message = completion.choices[0].message
        
        if message.parsed:
            print("--- Successfully received structured output ---")
            person = message.parsed
            
            # Print the structured data
            print("\nExtracted Data:")
            print(f"Name: {person.name}")
            print(f"Age: {person.age}")
            print(f"Height: {person.height}")
            print(f"Is Student: {person.is_student}")
            print(f"Hobbies: {', '.join(person.hobbies) if person.hobbies else 'None'}")
            
            if person.address:
                print(f"Address: {person.address.street}, {person.address.city}, {person.address.zip_code}")
            
            print(f"Test Scores: {person.scores if person.scores else 'None'}")
            print(f"Metadata: {person.metadata if person.metadata else 'None'}")
        else:
            print("Error: Model did not return parsed data as expected.")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 