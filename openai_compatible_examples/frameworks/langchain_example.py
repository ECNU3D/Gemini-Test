import os
from dotenv import load_dotenv
# Note: Ensure you have installed langchain-openai
# pip install langchain-openai
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.exceptions import LangChainException

# Load environment variables from .env file
load_dotenv()

# Get API details from environment variables
api_base_url = os.getenv("OPENAI_API_BASE")
api_key = os.getenv("OPENAI_API_KEY", "dummy-key") # Default to dummy key
model_name = os.getenv("MODEL_NAME", "default-model") # Provide a default model name

if not api_base_url:
    raise ValueError("OPENAI_API_BASE environment variable not set.")

print(f"--- Configuring LangChain ChatOpenAI ---")
print(f"Base URL: {api_base_url}")
print(f"Model: {model_name}")
print("API Key: Using provided key (or dummy key)")
print("---")

try:
    # Instantiate ChatOpenAI with custom endpoint configuration
    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base=api_base_url,
        temperature=0.7,
        max_tokens=100
    )

    # Prepare the input message
    messages = [HumanMessage(content="Explain the difference between a virtual machine and a container.")]

    print("--- Sending request using LangChain ---")
    print(f"Messages: {messages}")
    print("---")

    # Invoke the model
    response = llm.invoke(messages)

    print("--- LangChain Response --- ")
    # The response object is typically an AIMessage
    print(f"Type: {type(response)}")
    print(f"Content: {response.content}")
    if hasattr(response, 'response_metadata'):
        print(f"Metadata: {response.response_metadata}")
    print("---")

except LangChainException as e:
    print(f"A LangChain error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}") 