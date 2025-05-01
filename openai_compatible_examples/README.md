# OpenAI-Compatible API Examples

This project demonstrates various ways to interact with a custom LLM endpoint that is compatible with the OpenAI API specification.

## Features

*   Basic inference examples (`basic_inference/`) (single request, streaming, JSON mode) using both `requests` library and the official `openai` Python SDK.
*   Concurrent inference examples (`concurrent_inference/`) using `aiohttp` and the async `openai` SDK:
    *   Normal and streaming requests.
    *   Examples demonstrating manual exponential backoff for handling 429 rate limits.
    *   Examples demonstrating exponential backoff using the `tenacity` library decorator (retries initial request for normal & streaming).
*   Framework integration examples (`frameworks/`) with LangChain and LlamaIndex.
*   Multimodal examples (`multimodal/`) demonstrating how to:
    *   Send image data (text + image) to the chat completions endpoint.
    *   Send audio data for transcription (speech-to-text).

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
        *   `MODEL_NAME`: (Optional) The name of the model you want to use for chat completions, if your endpoint hosts multiple models (e.g., `gpt-4`). Vision models usually needed for image inputs.
        *   `TRANSCRIPTION_MODEL_NAME`: (Optional) The name of the model to use for audio transcriptions (e.g., `whisper-1`). Defaults to `whisper-1` in the scripts if not set.
        *   `IMAGE_PATH`: (Required for image examples) The path to a sample image file (e.g., `images/sample.jpg`).
        *   `AUDIO_PATH`: (Required for transcription examples) The path to a sample audio file (e.g., `audio/sample.wav`).
    *   **Proxy Configuration (Optional):** If you are behind a corporate proxy, you can configure it by setting the standard `HTTP_PROXY` and `HTTPS_PROXY` environment variables in the `.env` file or your shell. The `requests` library and the `openai` SDK (via `httpx`) will automatically pick them up.
        ```dotenv
        # Example Proxy Settings in .env
        # HTTP_PROXY="http://your-proxy.com:8080"
        # HTTPS_PROXY="http://user:password@your-proxy.com:8080"
        # NO_PROXY="localhost,127.0.0.1,your-internal-domain.com"
        ```

## Running the Examples

Navigate to the root directory (`openai_compatible_examples`) and run the Python scripts using their full path:

```bash
# --- Basic Inference (Single Request Focus) --- #

# Single request (requests lib)
python basic_inference/requests_single.py

# Streaming request (requests lib)
python basic_inference/requests_stream.py

# JSON mode request (requests lib)
python basic_inference/requests_json.py

# Single request (OpenAI SDK)
python basic_inference/openai_sdk_single.py

# Streaming request (OpenAI SDK)
python basic_inference/openai_sdk_stream.py

# JSON mode request (OpenAI SDK)
python basic_inference/openai_sdk_json.py


# --- Concurrent Inference --- #

# Concurrent normal requests (aiohttp)
python concurrent_inference/requests_concurrent_normal.py

# Concurrent normal requests (aiohttp) with MANUAL BACKOFF/RETRY logic
python concurrent_inference/requests_concurrent_normal_backoff.py

# Concurrent normal requests (aiohttp) with TENACITY decorator
python concurrent_inference/requests_concurrent_normal_tenacity.py

# Concurrent streaming requests (aiohttp)
python concurrent_inference/requests_concurrent_stream.py

# Concurrent streaming requests (aiohttp) with MANUAL BACKOFF/RETRY logic
python concurrent_inference/requests_concurrent_stream_backoff.py

# Concurrent streaming requests (aiohttp) with TENACITY decorator (retries initiation)
python concurrent_inference/requests_concurrent_stream_tenacity.py

# Concurrent normal requests (OpenAI SDK async)
python concurrent_inference/openai_sdk_concurrent_normal.py

# Concurrent normal requests (OpenAI SDK async) with MANUAL BACKOFF/RETRY logic
python concurrent_inference/openai_sdk_concurrent_normal_backoff.py

# Concurrent normal requests (OpenAI SDK async) with TENACITY decorator
python concurrent_inference/openai_sdk_concurrent_normal_tenacity.py

# Concurrent streaming requests (OpenAI SDK async)
python concurrent_inference/openai_sdk_concurrent_stream.py

# Concurrent streaming requests (OpenAI SDK async) with MANUAL BACKOFF/RETRY logic
python concurrent_inference/openai_sdk_concurrent_stream_backoff.py

# Concurrent streaming requests (OpenAI SDK async) with TENACITY decorator (retries initiation)
python concurrent_inference/openai_sdk_concurrent_stream_tenacity.py


# --- Framework Integration --- #

# LangChain example
python frameworks/langchain_example.py

# LlamaIndex example (using OpenAILike)
python frameworks/llamaindex_example.py


# --- Multimodal --- #

# Image request (requests lib)
# (Ensure IMAGE_PATH is set in .env)
python multimodal/requests_image.py

# Image request (OpenAI SDK)
# (Ensure IMAGE_PATH is set in .env)
python multimodal/openai_sdk_image.py

# Audio transcription request (requests lib)
# (Ensure AUDIO_PATH is set in .env)
python multimodal/requests_transcription.py

# Audio transcription request (OpenAI SDK)
# (Ensure AUDIO_PATH is set in .env)
python multimodal/openai_sdk_transcription.py