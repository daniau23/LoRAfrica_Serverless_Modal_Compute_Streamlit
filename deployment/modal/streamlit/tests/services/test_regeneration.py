"""Unit tests for services.regeneration module."""

import pytest
from unittest.mock import patch, MagicMock
from services.regeneration import handle_regeneration

class TestHandleRegeneration:
    """Tests for handle_regeneration() function."""

    def test_handle_regeneration_creates_regen_id_if_none(self, mock_streamlit):
        mock_streamlit.session_state.regen_id = None
        with patch("services.regeneration.generate_response"):
            handle_regeneration("Test prompt")
            assert mock_streamlit.session_state.regen_id is not None

    def test_handle_regeneration_preserves_existing_regen_id(self, mock_streamlit):
        mock_streamlit.session_state.regen_id = "existing-id"
        with patch("services.regeneration.generate_response"):
            handle_regeneration("Test prompt")
            assert mock_streamlit.session_state.regen_id == "existing-id"

    def test_handle_regeneration_increments_regen_index(self, mock_streamlit):
        mock_streamlit.session_state.regen_index = 1
        with patch("services.regeneration.generate_response"):
            handle_regeneration("Test prompt")
            # 1 + 1 = 2
            assert mock_streamlit.session_state.regen_index == 2

    def test_handle_regeneration_calls_generate_response(self, mock_streamlit):
        """Standard verification of the regeneration call flow."""
        mock_streamlit.session_state.regen_id = "uuid-test"
        mock_streamlit.session_state.regen_index = 1
        
        with patch("services.regeneration.generate_response") as mock_gen:
            handle_regeneration("Original prompt")
            
            mock_gen.assert_called_once()
            args, kwargs = mock_gen.call_args
            
            prompt_val = args[0] if args else kwargs.get("prompt")
            assert prompt_val == "Original prompt"
            assert kwargs.get("regeneration_id") == "uuid-test"
            assert kwargs.get("regeneration_index") == 2

    def test_handle_regeneration_returns_new_response(self, mock_streamlit):
        with patch("services.regeneration.generate_response", return_value="New Response"):
            result = handle_regeneration("Prompt")
            assert result == "New Response"

    def test_handle_regeneration_uses_override_temp(self, mock_streamlit):
        with patch("services.regeneration.generate_response") as mock_gen:
            handle_regeneration("Prompt", temp_override=0.9)
            _, kwargs = mock_gen.call_args
            assert kwargs.get("temp_override") == 0.9

    def test_handle_regeneration_always_uses_lora(self, mock_streamlit):
        with patch("services.regeneration.generate_response") as mock_gen:
            handle_regeneration("Prompt")
            _, kwargs = mock_gen.call_args
            assert kwargs.get("use_lora") is True