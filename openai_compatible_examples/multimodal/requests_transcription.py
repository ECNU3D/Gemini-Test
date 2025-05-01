import os
import requests
import json
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Get API details and audio path from environment variables
api_base = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
# Model name for transcription - often specified in the endpoint logic, 
# but can be passed if the API supports it (check your endpoint docs)
model_name = os.getenv("TRANSCRIPTION_MODEL_NAME", "whisper-1") # Default or specific model
audio_path = os.getenv("AUDIO_PATH")

if not api_base:
    raise ValueError("OPENAI_API_BASE environment variable not set.")
if not audio_path:
    raise ValueError("AUDIO_PATH environment variable not set. Please provide path to an audio file.")
if not os.path.exists(audio_path):
    raise FileNotFoundError(f"Audio file not found at: {audio_path}")

# Define the endpoint URL (ensure it ends with /v1)
transcriptions_url = f"{api_base.rstrip('/')}/audio/transcriptions"

# Define headers (Authorization only, Content-Type is set by requests for files)
headers = {
    "Authorization": f"Bearer {api_key}"
}

# Prepare the multipart/form-data payload
files = {
    'file': (os.path.basename(audio_path), open(audio_path, 'rb')),
}
# Add the model name to the data part of the multipart request
# (Check if your specific API requires the model in the form data)
data = {
    'model': model_name
}

print(f"--- Sending transcription request using requests --- ")
print(f"Target URL: {transcriptions_url}")
print(f"Audio File: {audio_path}")
print(f"Model specified: {model_name}")
print("---")

start_time = time.time()
try:
    # Open the file in binary mode and send the request
    with open(audio_path, 'rb') as audio_file:
        files = {
            'file': (os.path.basename(audio_path), audio_file),
        }
        response = requests.post(transcriptions_url, headers=headers, files=files, data=data)

    end_time = time.time()
    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

    # Process the successful response
    transcription_result = response.json()

    print(f"--- Transcription Response (requests) --- ({end_time - start_time:.2f}s)")
    print(f"Status Code: {response.status_code}")
    # The transcription text is usually in the 'text' field
    print(f"Transcription: {transcription_result.get('text')}")
    # print(f"Full Response JSON: {json.dumps(transcription_result, indent=2)}") # Uncomment to see full response
    print("---")

except requests.exceptions.RequestException as e:
    end_time = time.time()
    print(f"\n--- Error during requests transcription --- ({end_time - start_time:.2f}s)")
    print(f"Error: {e}")
    if e.response is not None:
        print(f"Status Code: {e.response.status_code}")
        try:
            print(f"Response Body: {e.response.json()}")
        except json.JSONDecodeError:
            print(f"Response Body: {e.response.text}")
    print("---")
except Exception as e:
    end_time = time.time()
    print(f"\n--- An unexpected error occurred --- ({end_time - start_time:.2f}s)")
    print(f"Error: {e}")
    print("---") 