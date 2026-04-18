import requests  # Used to send HTTP requests to your backend model
import json  # Used to parse streamed JSON responses

# Import centralized config
from config.settings import URL, MAX_TOKENS, TEMPERATURE  

def stream_response(
    prompt,  # User input text
    use_lora,  # Whether to use fine-tuned LoRAfrica model
    temp_override=None,  # Optional override for temperature
    regenerate=False,  # Flag to indicate regeneration mode
    regeneration_id=None,  # Unique ID to track regeneration sessions
    regeneration_index=0  # Counter for number of regenerations
):
    
    payload = {
        "prompt": prompt,
        "use_lora": use_lora,
        "max_tokens": MAX_TOKENS,
        # include temp_override if provided (for regeneration), 
        # otherwise use default
        "temperature": temp_override if temp_override is not None else TEMPERATURE,
        "stream": True, # Enable streaming response (token-by-token)
        "regenerate": regenerate,
        "regeneration_id": regeneration_id,
        "regeneration_index": regeneration_index
    }

    # Send POST request to model backend with streaming enabled
    response = requests.post(URL, json=payload, stream=True)

    # If API fails, raise error (handled upstream)
    if response.status_code != 200:
        raise Exception("Error generating response.")

    # Iterate over streamed response line-by-line
    for line in response.iter_lines():
        if not line:
            continue # Skip empty lines

        # Convert bytes → string
        line = line.decode("utf-8")

        # Backend sends data in "data: {...}" format (SSE-like)
        if line.startswith("data: "):
            # Remove "data: " prefix to get raw JSON string
            data = line[6:].strip() 

            # Check for end of stream signal (custom convention)
            if data == "[DONE]":
                break
            # Parse JSON and extract the generated token
            try:
                chunk_json = json.loads(data)
                token = chunk_json["choices"][0]["delta"].get("content", "")
                # Yield the token back to the caller 
                # (Streamlit UI) for real-time display
                yield token
            except json.JSONDecodeError:
                # Ignore malformed chunks
                # If JSON parsing fails, 
                # skip this chunk (could log if desired)
                continue
