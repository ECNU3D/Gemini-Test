import os
from openai import OpenAI, APIError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Default to a dummy key if not set
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

print(f"--- Configuring OpenAI SDK ---")
print(f"Base URL: {api_base_url}")
print(f"Model: {model_name}")
print("API Key: Using provided key (or dummy key)")
print("---")

# Configure the OpenAI client to point to your local endpoint
client = OpenAI(
    base_url=api_base_url,
    api_key=api_key,
)

# Define the messages payload
messages = [
    {"role": "user", "content": "Hello! Can you explain the concept of API compatibility briefly?"}
]

print("--- Sending request using OpenAI SDK ---")
print(f"Messages: {messages}")
print("---")

try:
    # Make the API call
    chat_completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=100,
        temperature=0.7,
    )

    print("--- Full Response Object ---")
    # The response object is a Pydantic model, print its dict representation
    print(chat_completion.model_dump_json(indent=2))
    print("---")

    # Extract and print the message content
    if chat_completion.choices:
        message = chat_completion.choices[0].message
        if message and message.content:
            print(f"Assistant's Response: {message.content}")
        else:
            print("Could not find message content in the response.")
    else:
        print("No choices found in the response.")

except APIError as e:
    # Handle API errors (e.g., connection issues, authentication problems)
    print(f"An API error occurred: {e}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response}")
except Exception as e:
    # Handle other potential errors
    print(f"An unexpected error occurred: {e}") 