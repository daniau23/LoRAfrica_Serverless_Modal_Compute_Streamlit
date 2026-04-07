import requests
import json

URL = "https://cdpqjzmsu5kx5u-7860.proxy.runpod.net/benchmarks"

payload = {
    "input_tokens": 64,
    "generated_tokens": 64,
    "num_prompts": 1,
    "batch_size": 1,
    "warmup_counts": 0
}

print(f"Sending request to: {URL}")

try:
    # 1. Get the raw response object first
    response = requests.post(URL, json=payload, timeout=120)
    
    # 2. Check if the server actually returned a 200 OK
    # If this fails, it will print the HTML error (404/504)
    response.raise_for_status() 
    
    # 3. ONLY NOW parse as JSON
    results = response.json()
    
    print("Response received successfully:")
    print(json.dumps(results, indent=4))

except requests.exceptions.HTTPError as http_err:
    print(f"HTTP Error: {http_err}")
    print(f"Server sent back: {response.text[:500]}") # Show the error page content
except Exception as e:
    print(f"Logic Error: {e}")