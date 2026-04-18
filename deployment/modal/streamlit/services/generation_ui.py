import streamlit as st # UI library for building the web app

def render_stream(token_generator):
    # Accumulates final full response text
    full_response = ""
    # Create assistant chat message container in UI
    with st.chat_message("assistant"):
        # Placeholder that updates dynamically 
        # as new tokens arrive
        response_container = st.empty()

        # For error handling during generation, 
        # we wrap the token iteration in a try-except block
        try:
            for token in token_generator:
                full_response += token
                # Show a "typing" indicator (▌) while generating
                response_container.markdown(full_response + "▌")
            
            # Once generation is complete, 
            # show the full response without the "typing" indicator
            response_container.markdown(full_response)

        except Exception as e:
            st.error(f"Error during generation: {e}")
            return "Error generating response."
    # Return the full response
    #  text once generation is done (or if an error occurs)
    return full_response