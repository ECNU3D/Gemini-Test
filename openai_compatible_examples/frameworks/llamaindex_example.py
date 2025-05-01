import os
from dotenv import load_dotenv
# Note: Ensure you have installed llama-index-llms-openai
# pip install llama-index-llms-openai
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import CompletionResponse

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Default to dummy key
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

print(f"--- Configuring LlamaIndex OpenAI LLM ---")
print(f"Base URL: {api_base_url}")
print(f"Model: {model_name}")
print("API Key: Using provided key (or dummy key)")
print("---")

try:
    # Instantiate the OpenAI LLM from LlamaIndex
    # Note: LlamaIndex uses 'api_base' instead of 'openai_api_base'
    llm = OpenAI(
        model=model_name,
        api_key=api_key,
        api_base=api_base_url,
        temperature=0.7,
        max_tokens=150
    )

    # Define the prompt
    prompt = "What are the main benefits of using a framework like LlamaIndex or LangChain?"

    print("--- Sending request using LlamaIndex ---")
    print(f"Prompt: {prompt}")
    print("---")

    # Use the complete method for a simple text completion
    # For chat models/endpoints, use .chat() instead:
    # from llama_index.core.llms import ChatMessage
    # response = llm.chat([ChatMessage(role="user", content=prompt)])
    response: CompletionResponse = llm.complete(prompt)

    print("--- LlamaIndex Response --- ")
    print(f"Type: {type(response)}")
    print(f"Text: {response.text}")
    if response.raw:
        print(f"Raw Response: {response.raw}")
    print("---")

except Exception as e:
    # Catching a general exception as specific LlamaIndex errors might vary
    print(f"An error occurred: {e}") 