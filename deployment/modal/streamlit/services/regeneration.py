import uuid  # Used to generate unique regeneration session IDs
import streamlit as st  # Access session state
from services.generation import generate_response  # Reuse generation logic
from utils.constants import DEFAULT_REGEN_TEMP  # Configurable regen temp

# Regeneration Logic (triggered by Regenerate button)
def handle_regeneration(user_prompt, temp_override=DEFAULT_REGEN_TEMP):
    
    # Ensure a persistent regeneration ID exists
    # This helps backend track regeneration sequences
    # If no regen_id exists in session state, create a new one
    cond = ("regen_id" not in st.session_state) or (st.session_state.regen_id is None)
    if cond:
        st.session_state.regen_id = str(uuid.uuid4())
    
    # Increment regeneration index to track how many times
    #  we've regenerated for this prompt
    st.session_state.regen_index += 1

    # Call the same generation function but 
    # with regeneration flags and temp override
    new_response = generate_response(
        user_prompt,
        use_lora=True,  # Regeneration should use LoRAfrica model
        temp_override=temp_override,
        regenerate=True,
        regeneration_id=st.session_state.regen_id,
        regeneration_index=st.session_state.regen_index
    )

    return new_response