# OpenAI-Compatible API Examples

This project demonstrates various ways to interact with a custom LLM endpoint that is compatible with the OpenAI API specification.

## Features

*   Basic inference examples (single request, streaming, JSON mode) using both `requests` library and the official `openai` Python SDK.
*   Integration examples with popular LLM frameworks: LangChain and LlamaIndex.
*   Multimodal examples demonstrating how to send image data (using base64 encoding) to the endpoint.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd openai_compatible_examples
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    *   Copy the `.env.example` file to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and add your specific endpoint details:
        *   `OPENAI_API_BASE`: The base URL of your OpenAI-compatible endpoint (e.g., `http://localhost:8000/v1`).
        *   `OPENAI_API_KEY`: Your API key (if required by your endpoint, can often be set to a placeholder like "dummy-key").
        *   `MODEL_NAME`: (Optional) The name of the model you want to use, if your endpoint hosts multiple models (e.g., `gpt-4`).
        *   `IMAGE_PATH`: (Optional, for multimodal examples) The path to a sample image file (e.g., `images/sample.jpg`).

## Running the Examples

Navigate to the specific example directory and run the Python scripts:

```bash
# Example: Run the basic single request using the openai SDK
python basic_inference/openai_sdk_single.py

# Example: Run the LangChain example
python frameworks/langchain_example.py
```

Refer to the comments within each script for more details. 