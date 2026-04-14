"""
Test client for Modal v1-chat-completions endpoint.

Usage:
    python client.py --prompt "Your question here" --model lora --stream
    python client.py                        # Interactive mode
    python client.py --stream               # Interactive Streaming Mode

Examples:
    python client.py --stream --model base --prompt "Briefly detail the significance story of the Igbo god Amadioha?"
    python client.py --stream --model lora --prompt "Briefly detail the significance story of the Igbo god Amadioha?"
    python client.py --model lora --prompt "Briefly detail the significance story of the Igbo god Amadioha?"
    # This will use the lora model
    python client.py --stream --prompt "Briefly detail the significance story of the Igbo god Amadioha?"
    python client.py  --prompt "Briefly detail the significance story of the Igbo god Amadioha?"
    # base model
    python client.py --model base  --prompt "Briefly detail the significance story of the Igbo god Amadioha?"
    python client.py --model base  --prompt "My name is Daniel I live in USA, my email is dan@gmail.com?. here is my phone +234813344576 and here is my ppsn 1234567FA and my zip code D02 XY45 and passport number PA1234567
"""

import argparse
import requests
import json 
from dotenv import load_dotenv
import os

# Configure


# ---------------------
# Configuration
# ---------------------
# Loading Environment Variables
load_dotenv('.env')
URL = os.getenv("MODAL_URL")
# use a .txt for your system prompt in the .env file, e.g. SYSTEM_PROMPT=system_prompt.txt
# proper opening and closing of the file to read the system prompt content into a variable
with open(os.getenv("SYSTEM_PROMPT"), 'r') as f:
    SYSTEM_PROMPT = f.read()
# Now fixed the issue with SYSTEM_PROMPT not being defined. 
# It should now print the content of the system prompt file specified in the .env file.
# print(SYSTEM_PROMPT) 

# ---------------------
# Helpers
# ---------------------
def create_payload(prompt: str, use_lora: bool, max_tokens: int = 128, stream: bool = False):
    """Helper function to create the payload for the API request."""
    
    return {
        "prompt": prompt,
        "use_lora": use_lora,
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "stream": stream
    }

def send_request(prompt: str, use_lora: bool, max_tokens: int = 128):
    """Send a single request to the API and return the full response."""
    payload = create_payload(prompt, use_lora, max_tokens, stream=False)
    response = requests.post(URL, json=payload)
    if response.status_code == 200:
        data = response.json()
        return data.get("choices", [{"message": {"content": data.get("response", "")}}])[0]["message"]["content"]
    else:
        print(f"Error: {response.status_code} | {response.text}")
        return ""

def send_request_stream(prompt: str, use_lora: bool = True, max_tokens: int = 128):
    """Send a request to the API and print the response as it streams in."""
    payload = {
        "prompt": prompt,
        "use_lora": use_lora,
        "max_tokens": max_tokens,
        "temperature": 0.1,
        "stream": True
    }
    response = requests.post(URL, json=payload, stream=True)
    if response.status_code != 200:
        print(f"Error: {response.status_code} | {response.text}")
        return

    # Process streaming response
    for line in response.iter_lines():
        if not line:
            continue
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        if line.startswith("data: "):
            data = line[6:].strip() 
            if data == "[DONE]":
                break
            try:
                # Assuming the server sends data in OpenAI stream format, we need to parse the JSON and extract the content
                chunk_json = json.loads(data)
                # Extract the actual generated content
                content = chunk_json["choices"][0]["delta"].get("content", "")
                print(content, end="", flush=True)
            except json.JSONDecodeError:
                # Just print raw data if not JSON
                print(data, end="", flush=True)
    print()


# ---------------------
# Main
# ---------------------
def main():
    # Argument Parser for CMD
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, default=None, help="Text prompt for the model")
    parser.add_argument("--model", choices=["base", "lora"], default="lora", help="Choose model variant")
    parser.add_argument("--stream", action="store_true", help="Enable streaming output")
    parser.add_argument("--max-tokens", type=int, default=128, help="Maximum tokens for generation")
    args = parser.parse_args()

    use_lora = args.model == "lora"

    if args.prompt:
        # Single request
        if args.stream:
            print("Bot: ", end="", flush=True)
            send_request_stream(args.prompt, use_lora, args.max_tokens)
        else:
            response = send_request(args.prompt, use_lora, args.max_tokens)
            print(f"Bot: {response}")
    else:
        # Interactive Chat Mode
        print("Interactive Mode. Type 'quit' or 'exit' to stop.\n")
        while True:
            try:
                user_input = input("You: ").strip()
                if user_input.lower() in ["quit", "exit"]:
                    print("Goodbye!")
                    break
                if not user_input:
                    continue

                if args.stream: # Streaming mode
                    print("Bot: ", end="", flush=True)
                    send_request_stream(user_input, use_lora, args.max_tokens)
                else: # Single response mode
                    response = send_request(user_input, use_lora, args.max_tokens)
                    print(f"Bot: {response}\n")
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

if __name__ == "__main__":
    main()