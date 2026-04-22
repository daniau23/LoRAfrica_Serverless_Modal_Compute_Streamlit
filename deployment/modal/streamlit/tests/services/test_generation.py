"""Unit tests for services.generation module."""

import pytest
from unittest.mock import MagicMock, patch
from services.generation import generate_response

class TestGenerateResponse:
    """Tests for generate_response() function."""

    def test_generate_response_success_with_lora(self, sample_full_response):
        with patch("services.generation.stream_response") as mock_stream, \
             patch("services.generation.render_stream", return_value=sample_full_response):
            
            mock_stream.return_value = iter(["token1", "token2"])
            result = generate_response(prompt="Tell me about Africa", use_lora=True)

            assert result == sample_full_response
            mock_stream.assert_called_once()
            
            # Safe argument checking
            args, kwargs = mock_stream.call_args
            prompt_val = args[0] if args else kwargs.get("prompt")
            assert prompt_val == "Tell me about Africa"

    def test_generate_response_without_lora(self):
        with patch("services.generation.stream_response") as mock_stream, \
             patch("services.generation.render_stream", return_value="response"):
            
            mock_stream.return_value = iter(["token"])
            generate_response(prompt="Question", use_lora=False)

            _, kwargs = mock_stream.call_args
            assert kwargs.get("use_lora") is False

    def test_generate_response_with_temp_override(self):
        with patch("services.generation.stream_response") as mock_stream, \
             patch("services.generation.render_stream", return_value="response"):
            
            mock_stream.return_value = iter(["token"])
            generate_response(prompt="Q", use_lora=True, temp_override=0.5)

            _, kwargs = mock_stream.call_args
            assert kwargs.get("temp_override") == 0.5

    def test_generate_response_with_regeneration_flags(self):
        with patch("services.generation.stream_response") as mock_stream, \
             patch("services.generation.render_stream", return_value="new response"):
            
            mock_stream.return_value = iter(["token"])
            generate_response(
                prompt="Q", 
                use_lora=True, 
                regenerate=True, 
                regeneration_id="uuid-123", 
                regeneration_index=1
            )

            _, kwargs = mock_stream.call_args
            assert kwargs.get("regenerate") is True
            assert kwargs.get("regeneration_id") == "uuid-123"
            assert kwargs.get("regeneration_index") == 1

    def test_generate_response_exception_handling(self, mock_streamlit):
        with patch("services.generation.stream_response") as mock_stream:
            mock_stream.side_effect = Exception("API connection failed")
            result = generate_response(prompt="Q", use_lora=True)

            mock_streamlit.error.assert_called_once()
            assert result == "Error generating response."

    # This is the specific test that was failing in your output
    def test_handle_regeneration_calls_generate_response(self, mock_streamlit):
        """Fixes the KeyError: 'prompt' by checking both args and kwargs."""
        mock_streamlit.session_state.regen_id = "uuid-test"
        mock_streamlit.session_state.regen_index = 1
        
        with patch("services.regeneration.generate_response") as mock_gen:
            from services.regeneration import handle_regeneration
            handle_regeneration("Original prompt")
            
            mock_gen.assert_called_once()
            args, kwargs = mock_gen.call_args
            
            # Use safe access to avoid KeyError
            prompt_val = args[0] if args else kwargs.get("prompt")
            assert prompt_val == "Original prompt"
            assert kwargs.get("regeneration_index") == 2