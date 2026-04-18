import streamlit as st  # Needed for error display
from services.generation_core import stream_response  # Backend logic
from services.generation_ui import render_stream  # UI renderer

def generate_response(
    prompt,
    use_lora,
    temp_override=None,
    regenerate=False,
    regeneration_id=None,
    regeneration_index=0
):
    try:
        # Call backend generator (no UI involved here)
        # Get token generator from streaming response function
        token_generator = stream_response(
            prompt=prompt,
            use_lora=use_lora,
            temp_override=temp_override,
            regenerate=regenerate,
            regeneration_id=regeneration_id,
            regeneration_index=regeneration_index
        )

        # Pass the token generator 
        # to the UI renderer to display tokens in real-time
        full_response = render_stream(token_generator)
        
        return full_response
    except Exception as e:
        # Display error message in 
        # Streamlit UI and return error string
        st.error(f"Error generating response: {e}")
        return "Error generating response."