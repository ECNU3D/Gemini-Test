import os

os.environ['GOOGLE_CLOUD_PROJECT'] = 'lab-eas-gcp-eval'
os.environ['GOOGLE_CLOUD_LOCATION'] = 'us-central1'
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'True'

from google import genai
from google.genai.types import HttpOptions

client = genai.Client(http_options=HttpOptions(api_version="v1"))
response = client.models.generate_content(
    model="gemini-2.0-flash-001",
    contents="How does AI work?",
)
print(response.text)