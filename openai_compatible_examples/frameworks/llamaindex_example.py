import os
from dotenv import load_dotenv
# Note: Ensure you have installed llama-index-llms-openai-like
# pip install llama-index-llms-openai-like
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.llms import ChatMessage, ChatResponse

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

try:
    # Instantiate the OpenAILike LLM from LlamaIndex
    llm = OpenAILike(
        model=model_name,
        api_key=api_key,
        api_base=api_base_url,
        is_chat_model=True,
        temperature=0.7,
        max_tokens=150
    )

    # Define the prompt
    prompt = "What are the main benefits of using a framework like LlamaIndex or LangChain?"
    messages = [ChatMessage(role="user", content=prompt)]

    print("--- Sending request using LlamaIndex (OpenAILike) ---")
    print(f"Messages: {messages}")
    print("---")

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