"""
Shared fixtures and mocks for pytest test suite.
Provides common setup for Streamlit app testing, including
mocked session state, API responses, and Streamlit components.
"""

import pytest
from unittest.mock import MagicMock, patch
import json
import copy
import os

# --- Hybrid Session State Class ---

class SessionState(dict):
    """
    Hybrid session state:
    - Supports dict-style: state["key"]
    - Supports attribute-style: state.key
    """
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"'SessionState' object has no attribute '{item}'")

    def __setattr__(self, key, value):
        self[key] = value

# --- Streamlit Mocks & Isolation ---

@pytest.fixture
def mock_streamlit_session_state():
    """Blueprint for initial session state."""
    state = SessionState()
    state["messages"] = []
    state["regen_index"] = 0
    state["regen_id"] = None
    return state

@pytest.fixture
def mock_streamlit(mock_streamlit_session_state, monkeypatch):
    """
    Main fixture to mock Streamlit. 
    Uses deepcopy to solve the 'assert 2 == 1' leakage issue.
    """
    import services.generation
    import services.generation_ui
    import services.generation_core
    import services.regeneration
    import config.settings

    # THE FIX: Create a unique instance for THIS test only
    clean_state = copy.deepcopy(mock_streamlit_session_state)
    
    # FORCE RESET: Ensure any existing references are zeroed out
    clean_state["regen_index"] = 0
    
    mock_st = MagicMock()
    mock_st.session_state = clean_state
    mock_st.error = MagicMock()

    # Chat message context manager
    mock_chat_message = MagicMock()
    mock_chat_message.__enter__ = MagicMock(return_value=mock_chat_message)
    mock_chat_message.__exit__ = MagicMock(return_value=None)
    mock_st.chat_message = MagicMock(return_value=mock_chat_message)

    # UI Components
    mock_container = MagicMock()
    mock_st.empty = MagicMock(return_value=mock_container)
    mock_st.markdown = MagicMock()
    mock_st.rerun = MagicMock()
    mock_st.set_page_config = MagicMock()
    mock_st.title = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.chat_input = MagicMock()
    mock_st.button = MagicMock()
    mock_st.selectbox = MagicMock()

    def safe_patch(module, attr, value):
        if hasattr(module, attr):
            monkeypatch.setattr(module, attr, value)

    modules_to_patch = [
        services.generation,
        services.generation_ui,
        services.generation_core,
        services.regeneration,
        config.settings
    ]
    
    for module in modules_to_patch:
        safe_patch(module, "st", mock_st)

    return mock_st

# --- Data & Response Fixtures ---

@pytest.fixture
def sample_prompt():
    return "Tell me about African history"

@pytest.fixture
def sample_full_response():
    """REQUIRED by test_generation_flow_end_to_end"""
    return "African history is rich."

@pytest.fixture
def sample_streaming_response():
    """SSE-formatted tokens for streaming tests."""
    tokens = [
        {"choices": [{"delta": {"content": "African"}}]},
        {"choices": [{"delta": {"content": " history"}}]},
        {"choices": [{"delta": {"content": " is"}}]},
        {"choices": [{"delta": {"content": " rich"}}]},
        {"choices": [{"delta": {"content": "."}}]},
    ]
    return [f"data: {json.dumps(token)}\n".encode("utf-8") for token in tokens] + [
        b"data: [DONE]\n"
    ]

@pytest.fixture
def sample_malformed_json_response():
    """REQUIRED by test_generation_flow_with_malformed_json"""
    return [
        b'data: {"choices": [{"delta": {"content": "Valid"}}]}\n',
        b"data: {invalid json}\n",
        b'data: {"choices": [{"delta": {"content": " response"}}]}\n',
        b"data: [DONE]\n",
    ]

# --- Request Mocks ---

@pytest.fixture
def mock_requests_post(sample_streaming_response):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = sample_streaming_response
    with patch("requests.post", return_value=mock_response) as mock_post:
        yield mock_post

@pytest.fixture
def mock_requests_post_error():
    """REQUIRED by test_stream_response_api_error"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    with patch("requests.post", return_value=mock_response) as mock_post:
        yield mock_post

@pytest.fixture
def mock_requests_post_malformed(sample_malformed_json_response):
    """REQUIRED by test_stream_response_malformed_json_skipped"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = sample_malformed_json_response
    with patch("requests.post", return_value=mock_response) as mock_post:
        yield mock_post

# --- Utility Mocks ---

@pytest.fixture
def mock_uuid4():
    fixed_uuid = "550e8400-e29b-41d4-a716-446655440000"
    with patch("uuid.uuid4", return_value=fixed_uuid) as mock_uuid:
        yield mock_uuid

@pytest.fixture
def mock_dotenv_load():
    with patch("dotenv.load_dotenv") as mock_load:
        yield mock_load

@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("MODAL_URL", "http://test-modal-url:8000")
    yield