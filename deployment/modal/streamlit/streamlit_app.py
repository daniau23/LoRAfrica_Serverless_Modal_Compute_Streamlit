import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os

# Configure
# loading Environment Variables
load_dotenv('.env')
URL = os.getenv("MODAL_URL") or st.secrets["MODAL_URL"]

# If I wanted to use FastAPI as a proxy instead of calling Modal directly, I would set URL to my FastAPI endpoint, e.g.:
# ✅ Now pointing to FastAPI proxy (NOT Modal)
# URL = "http://localhost:8000/chat"
MAX_TOKENS = 128
TEMPERATURE = 0.1
# MAX_HISTORY = 5  # ✅ LIMIT HISTORY
# 5 user messages + 5 assistant messages = 10
MAX_TURNS = 5  # ✅ Keep last 5 turns (1 turn = user + assistant)



def trim_history(messages, max_turns=3):
    """
    Keep only the last N turns (1 turn = user + assistant).
    Ensures conversation starts with a user message.
    """
    if not messages:
        return []

    max_messages = max_turns * 2  # Each turn has 2 messages (user + assistant)
    # Trimmed 
    trimmed = messages[-max_messages:]  # <-- use slice, not single index


    # Ensure it starts with a user message
    if trimmed and trimmed[0]["role"] == "assistant":
        trimmed = trimmed[1:]

    return trimmed

# Page Setup
st.set_page_config(page_title="LoRAfrica Chat", layout="wide")
st.title("🌍 LoRAfrica - African History Assistant")

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Side Bar
st.sidebar.header("⚙️ Settings")

model_choice = st.sidebar.selectbox("Select a Model", ["LoRAfrica", "Base Model"],
                    help="Lora is the Model Dedicated to African History")
# use_lora = "lora" in model_choice.lower().strip() # if True, Lora Model will be used
# if True, LoRAfrica Model will be used, I believe this is better 
use_lora = True if model_choice == "LoRAfrica" else False 

# No more additional temperature input for now, keeping it fixed for concise output, but this can be re-enabled if needed
# # ✅ User-controlled temperature
# temperature_slider = st.sidebar.slider(
#     "Response Temperature",
#     min_value=0.0,
#     max_value=1.0,
#     value=0.1,  # default
#     step=0.05,
#     help="Higher values = more creative responses, lower = more deterministic"
# )

# temperature_input = st.sidebar.number_input(
#     "Temperature (type)",
#     min_value=0.0,
#     max_value=1.0,
#     value=temperature_slider,
#     step=0.01,
#     format="%.2f"
# )
# temperature = temperature_input

temperature = TEMPERATURE # for concise output
# ✅ Clear Chat button
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.rerun()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# User Input
if prompt := st.chat_input("I'm LoRAfrica, your African History Expert..."):
    # Append user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Send request to backend
    payload = {
        # "prompt": st.session_state.messages[-1]['content'],  # Send the latest user message as prompt
        "messages": st.session_state.messages, # Send the latest user message + preivous messages as prompt
        "use_lora": use_lora,
        "max_tokens": MAX_TOKENS,
        "temperature": temperature,
        "stream": True
    }

    # Streaming Response
    with st.chat_message("assistant"):
        
        response_container = st.empty()
        full_response = ""

        try:
            response = requests.post(URL, json=payload, stream=True)

            if response.status_code !=200: # Check request status code
                st.error(f"Error: {response.status_code} | {response.text}")

            else: # Streaming the response
                for line in response.iter_lines():

                    if not line:
                        continue
                    line = line.decode("utf-8")

                    if line.startswith("data: "):
                        data = line[6:].strip()

                        if data  == "[DONE]":
                            break
                        try: # Checking Json feedback
                            chunk_json = json.loads(data)
                            token  = chunk_json["choices"][0]["delta"].get("content", "") 

                            full_response += token

                            # Typing effect
                            response_container.markdown(full_response + "▌")
                        except json.JSONDecodeError:
                            continue
                    response_container.markdown(full_response)
        except Exception as e:
            st.error(f"Request failed: {e}")
            full_response = "Error generating response."

    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )
    # ✅ Enforce max history again
    # st.session_state.messages = st.session_state.messages[-MAX_HISTORY:]
    
    # ✅ Trim history again to enforce max turns after adding assistant
    st.session_state.messages = trim_history(
        st.session_state.messages,
        max_turns=MAX_TURNS # keep the last 10 messages (5 users + 5 assistant response)
    )