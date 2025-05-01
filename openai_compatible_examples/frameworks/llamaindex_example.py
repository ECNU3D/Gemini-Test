import os
import sys
from dotenv import load_dotenv
# Note: Ensure you have installed llama-index-llms-openai-like
# pip install llama-index-llms-openai-like
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.llms import ChatMessage, ChatResponse

# Add the parent directory (openai_compatible_examples) to sys.path
# to allow importing from the 'utils' module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from utils.auth_helpers import get_api_key # Use sync version

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Default to dummy key
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

print(f"--- Configuring LlamaIndex OpenAILike LLM ---")
print(f"Base URL: {api_base_url}")
print(f"Model: {model_name}")
print("API Key: Using provided key (or dummy key)")
print("---")

def main():
    print("--- Sending request using LlamaIndex (OpenAILike) ---")
    print(f"Base URL: {api_base_url}")
    print(f"Model: {model_name}")
    print("---")

    try:
        # Initialize OpenAILike LLM
        # API key is fetched dynamically *per request* below
        llm = OpenAILike(
            model=model_name,
            api_base=api_base_url,
            api_key="temp-key", # Placeholder, updated before request
            is_chat_model=True, # Crucial for using chat messages
            temperature=0.7,
            max_tokens=50,
            # api_version="v1" # Optional: Specify API version if needed by your endpoint
        )

        # Define the prompt
        prompt = "What are the main benefits of using a framework like LlamaIndex or LangChain?"
        messages = [ChatMessage(role="user", content=prompt)]

        # Fetch the latest API key and update the client
        llm.api_key = get_api_key()

        # Use the chat method for chat models/endpoints
        response: ChatResponse = llm.chat(messages)

        print("--- LlamaIndex Response --- ")
        print(f"Type: {type(response)}")
        if response.message:
            print(f"Content: {response.message.content}")
        else:
            print("No message content received.")
        if response.raw:
            print(f"Raw Response: {response.raw}")
        print("---")

    except Exception as e:
        # Catching a general exception as specific LlamaIndex errors might vary
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 