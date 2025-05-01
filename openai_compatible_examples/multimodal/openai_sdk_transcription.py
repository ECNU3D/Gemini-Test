import os
from openai import OpenAI, APIError # Use synchronous client for simplicity here
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Get API details and audio path from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
# Model name for transcription
model_name = os.getenv("TRANSCRIPTION_MODEL_NAME", "whisper-1") # Default or specific model
audio_path = os.getenv("AUDIO_PATH")

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")
if not audio_path:
    raise ValueError("AUDIO_PATH environment variable not set. Please provide path to an audio file.")
if not os.path.exists(audio_path):
    raise FileNotFoundError(f"Audio file not found at: {audio_path}")

# Configure the OpenAI client
# Ensure the base_url points to your v1 endpoint
client = OpenAI(
    base_url=api_base_url,
    api_key=api_key,
)

print(f"--- Sending transcription request using OpenAI SDK --- ")
print(f"Base URL: {api_base_url}")
print(f"Audio File: {audio_path}")
print(f"Model specified: {model_name}")
print("---")

start_time = time.time()
try:
    # Open the file in binary read mode
    with open(audio_path, "rb") as audio_file:
        # Call the audio transcriptions endpoint
        transcription = client.audio.transcriptions.create(
            model=model_name,
            file=audio_file
            # You can add other parameters like 'language', 'prompt', 'response_format', 'temperature'
            # language="en",
            # response_format="json" # default is json, others can be text, srt, verbose_json, vtt
        )

    end_time = time.time()

    print(f"--- Transcription Response (OpenAI SDK) --- ({end_time - start_time:.2f}s)")
    # The transcription object has a 'text' attribute
    print(f"Transcription: {transcription.text}")
    # print(f"Full Response Object: {transcription}") # Uncomment to see full response object
    print("---")

except APIError as e:
    end_time = time.time()
    print(f"\n--- OpenAI API Error --- ({end_time - start_time:.2f}s)")
    print(f"Status Code: {e.status_code}")
    print(f"Error Code: {e.code}")
    print(f"Message: {e.message}")
    print(f"Response: {e.response}")
    print("---")
except Exception as e:
    end_time = time.time()
    print(f"\n--- An unexpected error occurred --- ({end_time - start_time:.2f}s)")
    print(f"Error: {e}")
    print("---") 