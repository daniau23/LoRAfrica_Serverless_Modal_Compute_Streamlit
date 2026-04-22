"""Integration tests for Streamlit app generation workflows."""

import pytest
from unittest.mock import patch, MagicMock, call
import json


class TestGenerationFlow:
    """Integration tests for the complete generation flow."""

    def test_generation_flow_end_to_end(
        self, mock_streamlit, sample_streaming_response, sample_full_response
    ):
        """
        Test complete flow: prompt → stream_response → render_stream.
        Verifies token flow from API to UI display.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            from services.generation import generate_response

            result = generate_response(
                prompt="Tell me about Africa",
                use_lora=True,
            )

            # Verify final response matches expected
            assert result == sample_full_response

            # Verify API was called
            mock_post.assert_called_once()

    def test_generation_flow_with_temperature_override(
        self, mock_streamlit, sample_streaming_response
    ):
        """
        Test generation flow with temperature override.
        Verifies temp is passed through entire chain: generation → core → API.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            from services.generation import generate_response

            generate_response(
                prompt="Question",
                use_lora=False,
                temp_override=0.7,
            )

            # Verify temp in API payload
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["temperature"] == 0.7

    def test_generation_flow_streaming_tokens_displayed(
        self, mock_streamlit, sample_streaming_response
    ):
        """
        Test that streaming tokens are progressively displayed in UI.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            mock_container = MagicMock()
            mock_streamlit.empty.return_value = mock_container

            from services.generation import generate_response

            generate_response(
                prompt="Q",
                use_lora=True,
            )

            # Verify markdown called multiple times for progressive display
            assert mock_container.markdown.call_count > 0

    def test_generation_flow_error_handling(
        self, mock_streamlit
    ):
        """
        Test error handling across entire generation flow.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500  # API error
            mock_post.return_value = mock_response

            from services.generation import generate_response

            result = generate_response(
                prompt="Q",
                use_lora=True,
            )

            # Verify error handling
            assert result == "Error generating response."
            mock_streamlit.error.assert_called_once()

    def test_generation_flow_no_lora_model(
        self, mock_streamlit, sample_streaming_response
    ):
        """
        Test generation flow with base model (no LoRA).
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            from services.generation import generate_response

            generate_response(
                prompt="Q",
                use_lora=False,
            )

            # Verify use_lora=False in API call
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["use_lora"] is False

    def test_generation_flow_with_malformed_json(
        self, mock_streamlit, sample_malformed_json_response
    ):
        """
        Test generation flow gracefully handles malformed JSON in stream.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_malformed_json_response
            mock_post.return_value = mock_response

            from services.generation import generate_response

            result = generate_response(
                prompt="Q",
                use_lora=True,
            )

            # Should still return result (with valid tokens only)
            assert result == "Valid response"


class TestRegenerationFlow:
    """Integration tests for the regeneration workflow."""

    def test_regeneration_flow_creates_new_response(
        self, mock_streamlit, sample_streaming_response
    ):
        """
        Test complete regeneration flow: session state → regen → new response.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            from services.regeneration import handle_regeneration

            # Initial state
            mock_streamlit.session_state.regen_id = None
            mock_streamlit.session_state.regen_index = 0

            result = handle_regeneration("Original prompt")

            # Verify response generated
            assert result is not None
            # Verify session state mutated
            assert mock_streamlit.session_state.regen_id is not None
            assert mock_streamlit.session_state.regen_index == 1

    def test_regeneration_flow_uuid_persistence(
        self, mock_streamlit, sample_streaming_response
    ):
        """
        Test that regen_id persists across multiple regenerations.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            from services.regeneration import handle_regeneration

            # Initial state
            mock_streamlit.session_state.regen_id = None
            mock_streamlit.session_state.regen_index = 0

            # First regen
            handle_regeneration("Prompt")
            first_id = mock_streamlit.session_state.regen_id

            # Second regen
            handle_regeneration("Prompt")
            second_id = mock_streamlit.session_state.regen_id

            # IDs should be same
            assert first_id == second_id
            assert mock_streamlit.session_state.regen_index == 2

    def test_regeneration_flow_temp_override(
        self, mock_streamlit, sample_streaming_response
    ):
        """
        Test that temperature override flows through regeneration.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            from services.regeneration import handle_regeneration

            handle_regeneration("Prompt", temp_override=0.9)

            # Verify temp in API payload
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["temperature"] == 0.9

    def test_regeneration_flow_always_uses_lora(
        self, mock_streamlit, sample_streaming_response
    ):
        """
        Test that regeneration always uses LoRA model, even if base was used initially.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            from services.regeneration import handle_regeneration

            # Even though we don't explicitly pass use_lora to handle_regeneration,
            # it should force use_lora=True in generate_response
            handle_regeneration("Prompt")

            # Verify use_lora=True in API payload
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["use_lora"] is True

    def test_regeneration_flow_flags_correctly_set(
        self, mock_streamlit, sample_streaming_response
    ):
        """
        Test that regeneration flags are correctly set in API payload.
        """
        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_lines.return_value = sample_streaming_response
            mock_post.return_value = mock_response

            from services.regeneration import handle_regeneration

            mock_streamlit.session_state.regen_id = "uuid-test"
            mock_streamlit.session_state.regen_index = 1

            handle_regeneration("Prompt")

            # Verify regeneration flags
            call_args = mock_post.call_args
            payload = call_args.kwargs["json"]
            assert payload["regenerate"] is True
            assert payload["regeneration_id"] == "uuid-test"
            assert payload["regeneration_index"] == 2
