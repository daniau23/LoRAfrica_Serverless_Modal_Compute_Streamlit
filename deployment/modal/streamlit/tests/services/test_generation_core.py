"""Unit tests for services.generation_core module."""

import pytest
import json
from unittest.mock import MagicMock, patch
from services.generation_core import stream_response


class TestStreamResponse:
    """Tests for stream_response() function."""

    def test_stream_response_basic(self, mock_requests_post):
        """
        Test basic streaming response with valid JSON chunks.
        Verifies tokens are yielded correctly from SSE-like format.
        """
        tokens = list(
            stream_response(
                prompt="Test prompt",
                use_lora=True,
            )
        )

        # Should yield: "African", " history", " is", " rich", "."
        assert tokens == ["African", " history", " is", " rich", "."]
        mock_requests_post.assert_called_once()

    def test_stream_response_payload_structure(self, mock_requests_post):
        """Test that stream_response sends correct payload to API."""
        from config.settings import TEMPERATURE, MAX_TOKENS

        list(
            stream_response(
                prompt="Test",
                use_lora=True,
                temp_override=0.5,
            )
        )

        # Verify POST call payload
        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]

        assert payload["prompt"] == "Test"
        assert payload["use_lora"] is True
        assert payload["max_tokens"] == MAX_TOKENS
        assert payload["temperature"] == 0.5
        assert payload["stream"] is True
        assert payload["regenerate"] is False
        assert payload["regeneration_id"] is None
        assert payload["regeneration_index"] == 0

    def test_stream_response_default_temperature(self, mock_requests_post):
        """Test that default TEMPERATURE is used when temp_override is None."""
        from config.settings import TEMPERATURE

        list(
            stream_response(
                prompt="Test",
                use_lora=True,
                temp_override=None,
            )
        )

        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]
        assert payload["temperature"] == TEMPERATURE

    def test_stream_response_with_regeneration_flags(self, mock_requests_post):
        """Test that regeneration flags are included in payload."""
        list(
            stream_response(
                prompt="Test",
                use_lora=True,
                regenerate=True,
                regeneration_id="uuid-456",
                regeneration_index=2,
            )
        )

        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]
        assert payload["regenerate"] is True
        assert payload["regeneration_id"] == "uuid-456"
        assert payload["regeneration_index"] == 2

    def test_stream_response_api_error(self, mock_requests_post_error):
        """Test error handling when API returns non-200 status code."""
        with pytest.raises(Exception, match="Error generating response"):
            list(
                stream_response(
                    prompt="Test",
                    use_lora=True,
                )
            )

    def test_stream_response_empty_lines_skipped(self):
        """Test that empty lines in streamed response are skipped."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Include empty lines (b'') which should be skipped
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
            b"",  # Empty line - should be skipped
            b'data: {"choices": [{"delta": {"content": " World"}}]}\n',
            b"data: [DONE]\n",
        ]

        with patch("requests.post", return_value=mock_response):
            tokens = list(
                stream_response(
                    prompt="Test",
                    use_lora=True,
                )
            )

        assert tokens == ["Hello", " World"]

    def test_stream_response_malformed_json_skipped(self, mock_requests_post_malformed):
        """
        Test that malformed JSON chunks are skipped gracefully.
        Valid chunks before and after malformed chunks should still be processed.
        """
        tokens = list(
            stream_response(
                prompt="Test",
                use_lora=True,
            )
        )

        # Should yield only valid tokens, skipping malformed JSON
        assert tokens == ["Valid", " response"]

    def test_stream_response_done_signal_stops_iteration(self):
        """Test that [DONE] signal stops token iteration."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "Token1"}}]}\n',
            b'data: {"choices": [{"delta": {"content": "Token2"}}]}\n',
            b"data: [DONE]\n",
            # This should never be reached
            b'data: {"choices": [{"delta": {"content": "Token3"}}]}\n',
        ]

        with patch("requests.post", return_value=mock_response):
            tokens = list(
                stream_response(
                    prompt="Test",
                    use_lora=True,
                )
            )

        assert tokens == ["Token1", "Token2"]
        assert "Token3" not in tokens

    def test_stream_response_missing_content_field(self):
        """
        Test handling of delta objects without 'content' field.
        Should yield empty string for missing content.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices": [{"delta": {"content": "Start"}}]}\n',
            b'data: {"choices": [{"delta": {}}]}\n',  # No content field
            b'data: {"choices": [{"delta": {"content": "End"}}]}\n',
            b"data: [DONE]\n",
        ]

        with patch("requests.post", return_value=mock_response):
            tokens = list(
                stream_response(
                    prompt="Test",
                    use_lora=True,
                )
            )

        # Empty string yielded for missing content, but still accumulated
        assert tokens == ["Start", "", "End"]

    def test_stream_response_url_from_settings(self, mock_requests_post):
        """Test that URL is taken from config.settings."""
        from config.settings import URL

        list(
            stream_response(
                prompt="Test",
                use_lora=True,
            )
        )

        call_args = mock_requests_post.call_args
        assert call_args.args[0] == URL

    def test_stream_response_streaming_enabled(self, mock_requests_post):
        """Test that stream=True is always set in payload."""
        list(
            stream_response(
                prompt="Test",
                use_lora=True,
            )
        )

        call_args = mock_requests_post.call_args
        assert call_args.kwargs["stream"] is True

    def test_stream_response_complex_payload(self, mock_requests_post):
        """
        Test stream_response with all parameters set (comprehensive payload test).
        """
        list(
            stream_response(
                prompt="Complex test prompt",
                use_lora=False,
                temp_override=0.9,
                regenerate=True,
                regeneration_id="test-uuid-789",
                regeneration_index=3,
            )
        )

        call_args = mock_requests_post.call_args
        payload = call_args.kwargs["json"]

        assert payload == {
            "prompt": "Complex test prompt",
            "use_lora": False,
            "max_tokens": payload["max_tokens"],  # From settings
            "temperature": 0.9,
            "stream": True,
            "regenerate": True,
            "regeneration_id": "test-uuid-789",
            "regeneration_index": 3,
        }
