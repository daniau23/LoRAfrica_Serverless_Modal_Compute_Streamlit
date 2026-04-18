import streamlit as st
from dotenv import load_dotenv
import os

# Configure
# loading Environment Variables
load_dotenv('../.env')

# API endpoint:
# First try environment variable (local dev),
# fallback to Streamlit secrets (for deployment e.g. Streamlit Cloud)
URL = os.getenv("MODAL_URL") or st.secrets["MODAL_URL"]

# Maximum number of tokens to generate from the model
# Keeping it centralized makes tuning easier
MAX_TOKENS = 128

# Default temperature (controls randomness)
# Lower = more deterministic, higher = more creati
TEMPERATURE = 0.1