from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse  # ✅ FIX HERE
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

MODAL_URL = os.getenv("MODAL_URL")


@app.post("/chat")
async def chat(request: Request):
    body = await request.json()

    response = requests.post(
        MODAL_URL,
        json=body,
        stream=True
    )

    def generate():
        for chunk in response.iter_lines():
            if chunk:
                yield chunk + b"\n"

    # ✅ FIXED LINE
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


# Run using uvicorn proxy:app --reload