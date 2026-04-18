import streamlit as st  # Core UI framework

# Import modular components
from services.generation import generate_response
from services.regeneration import handle_regeneration
from config.settings import TEMPERATURE
from utils.constants import APP_TITLE, CHAT_INPUT_PLACEHOLDER


# Page Setup
st.set_page_config(page_title="LoRAfrica Chat", layout="wide")
st.title(APP_TITLE)

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

# Clear Chat button (UI only)
if st.sidebar.button("🗑️ Clear Chat"):
    st.session_state.messages = []
    st.session_state.last_prompt = None  # 🆕 reset
    st.session_state.regen_id = None  # 🆕 reset
    st.rerun() # Refresh app to reflect cleared chat

# Display Chat History (UI only)
for i, message in enumerate(st.session_state.messages):

    with st.chat_message(message['role']):
        st.markdown(message['content'])

        # 🆕 REGENERATE BUTTON (only for assistant messages)
        if message["role"] == "assistant":
            
            # Find previous user message
            if i > 0 and st.session_state.messages[i-1]["role"] == "user":
                user_prompt = st.session_state.messages[i-1]["content"]

                if st.button("🔁 Regenerate", key=f"regen_{i}"):

                    # Remove last assistant response
                    st.session_state.messages.pop(i)

                    # Regenerate response
                    new_response = handle_regeneration(
                        user_prompt
                        )

                    # Save regenerated response
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": new_response
                    })
                    # Refresh to show regenerated response
                    st.rerun()


# User/Chat Input box
if prompt := st.chat_input(CHAT_INPUT_PLACEHOLDER):

    # st.session_state.last_prompt = prompt  # 🆕

    # (recommended safety reset - optional but harmless)
    st.session_state.regen_index = 0

    # Save user's prompt in session state to maintain conversation history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user's prompt immediately in the chat UI
    with st.chat_message("user"):
        st.markdown(prompt)

    full_response = generate_response(prompt, use_lora=use_lora)

    # Save assistant's response in session state to
    # maintain conversation history
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response
        }
    )

    

# Next features 
# - Disable the ability to send another request when generation is not fully done
# - Edit prompts after sending (e.g., to fix typos) and regenerate based on edited prompt while keeping the same conversation thread