import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os
import uuid  

# Configure
# loading Environment Variables
load_dotenv('.env')
URL = os.getenv("MODAL_URL") or st.secrets["MODAL_URL"]

MAX_TOKENS = 128
TEMPERATURE = 0.1


# Page Setup
st.set_page_config(page_title="LoRAfrica Chat", layout="wide")
st.title("🌍 LoRAfrica - African History Assistant")

# Session State (UI only)
if "messages" not in st.session_state:
    st.session_state.messages = []

if "regen_index" not in st.session_state:
    st.session_state.regen_index = 0

# ✅ Initialise regen_id
if "regen_id" not in st.session_state:
    st.session_state.regen_id = None


# Side Bar
st.sidebar.header("⚙️ Settings")

model_choice = st.sidebar.selectbox(
    "Select a Model",
    ["lora", "base"],
    help="Lora is the Model Dedicated to African History"
)
use_lora = "lora" in model_choice.lower().strip()

temperature = TEMPERATURE

# Clear Chat button (UI only)
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.session_state.last_prompt = None  # 🆕 reset
    st.rerun()


# Function to call backend (REUSED for normal + regenerate)
def generate_response(
    prompt,
    temp_override=None,
    regenerate=False,
    regeneration_id=None,
    regeneration_index=0
):
    
    payload = {
        "prompt": prompt,
        "use_lora": use_lora,
        "max_tokens": MAX_TOKENS,
        # include temp_override if provided (for regeneration), 
        # otherwise use default
        "temperature": temp_override if temp_override is not None else temperature,
        "stream": True,
        "regenerate": regenerate,
        "regeneration_id": regeneration_id,
        "regeneration_index": regeneration_index
    }

    with st.chat_message("assistant"):
        response_container = st.empty()
        full_response = ""

        try:
            response = requests.post(URL, json=payload, stream=True)

            if response.status_code != 200:
                st.error(f"Error: {response.status_code} | {response.text}")
                return "Error generating response."

            for line in response.iter_lines():
                if not line:
                    continue

                line = line.decode("utf-8")

                if line.startswith("data: "):
                    data = line[6:].strip()

                    if data == "[DONE]":
                        break

                    try:
                        chunk_json = json.loads(data)
                        token = chunk_json["choices"][0]["delta"].get("content", "")

                        full_response += token
                        response_container.markdown(full_response + "▌")

                    except json.JSONDecodeError:
                        continue

                response_container.markdown(full_response)

        except Exception as e:
            st.error(f"Request failed: {e}")
            return "Error generating response."

    return full_response


# Regeneration Logic (triggered by Regenerate button)
def handle_regeneration(user_prompt, temp_override=0.3):
    
    # Create or reuse stable ID
    if st.session_state.regen_id is None:
        st.session_state.regen_id = str(uuid.uuid4())

    st.session_state.regen_index += 1

    new_response = generate_response(
        user_prompt,
        temp_override=temp_override,
        regenerate=True,
        regeneration_id=st.session_state.regen_id,
        regeneration_index=st.session_state.regen_index
    )

    return new_response


# Display Chat History (UI only)
for i, message in enumerate(st.session_state.messages):

    with st.chat_message(message['role']):
        st.markdown(message['content'])

        # 🆕 REGENERATE BUTTON (only for assistant messages)
        if message["role"] == "assistant":
            # find previous user message
            if i > 0 and st.session_state.messages[i-1]["role"] == "user":
                user_prompt = st.session_state.messages[i-1]["content"]

                if st.button("🔁 Regenerate", key=f"regen_{i}"):

                    # remove last assistant response
                    st.session_state.messages.pop(i)

                    # regenerate response
                    new_response = handle_regeneration(user_prompt)

                    # save updated response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": new_response
                    })

                    st.rerun()


# User Input
if prompt := st.chat_input("I'm LoRAfrica, your African History Expert..."):

    st.session_state.last_prompt = prompt  # 🆕

    # (recommended safety reset - optional but harmless)
    st.session_state.regen_index = 0

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    full_response = generate_response(prompt)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )