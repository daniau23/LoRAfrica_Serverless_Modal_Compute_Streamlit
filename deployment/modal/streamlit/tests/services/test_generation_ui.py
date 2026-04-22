"""Unit tests for services.generation_ui module."""

import pytest
from unittest.mock import MagicMock, patch, call
from services.generation_ui import render_stream


class TestRenderStream:
    """Tests for render_stream() function."""

    def test_render_stream_accumulates_tokens(self, mock_streamlit):
        """
        Test that render_stream accumulates tokens from generator into full response.
        """
        token_generator = iter(["Hello", " ", "World", "!"])

        result = render_stream(token_generator)

        assert result == "Hello World!"

    def test_render_stream_displays_typing_indicator(self, mock_streamlit):
        """
        Test that render_stream shows typing indicator (▌) while generating.
        """
        mock_container = mock_streamlit.empty.return_value
        mock_container.markdown = MagicMock()

        token_generator = iter(["Token"])

        render_stream(token_generator)

        # Verify markdown called with typing indicator
        calls = mock_container.markdown.call_args_list
        # Last call should be without typing indicator (final response)
        assert "▌" in calls[0][0][0]  # First call has typing indicator
        assert "▌" not in calls[-1][0][0]  # Last call no typing indicator

    def test_render_stream_removes_typing_indicator_at_end(self, mock_streamlit):
        """
        Test that final response displayed without typing indicator.
        """
        mock_container = mock_streamlit.empty.return_value
        mock_container.markdown = MagicMock()

        token_generator = iter(["This", " is", " final"])

        result = render_stream(token_generator)

        # Last markdown call should be the final response without ▌
        last_call = mock_container.markdown.call_args_list[-1][0][0]
        assert last_call == "This is final"
        assert "▌" not in last_call

    def test_render_stream_creates_chat_message(self, mock_streamlit):
        """Test that render_stream creates an assistant chat message."""
        token_generator = iter(["response"])

        render_stream(token_generator)

        # Verify st.chat_message called with "assistant"
        mock_streamlit.chat_message.assert_called_once_with("assistant")

    def test_render_stream_empty_generator(self, mock_streamlit):
        """Test render_stream with empty token generator."""
        token_generator = iter([])

        result = render_stream(token_generator)

        assert result == ""

    def test_render_stream_single_token(self, mock_streamlit):
        """Test render_stream with single token."""
        mock_container = mock_streamlit.empty.return_value
        mock_container.markdown = MagicMock()

        token_generator = iter(["SingleToken"])

        result = render_stream(token_generator)

        assert result == "SingleToken"
        # Should still update display twice: with and without typing indicator
        assert mock_container.markdown.call_count == 2

    def test_render_stream_long_response(self, mock_streamlit):
        """Test render_stream with longer response (many tokens)."""
        mock_container = mock_streamlit.empty.return_value
        mock_container.markdown = MagicMock()

        tokens = ["The", " ", "quick", " ", "brown", " ", "fox", " ", "jumps"]
        token_generator = iter(tokens)

        result = render_stream(token_generator)

        assert result == "The quick brown fox jumps"
        # markdown should be called len(tokens) + 1 times (once per token + final)
        assert mock_container.markdown.call_count == len(tokens) + 1

    def test_render_stream_exception_in_generator(self, mock_streamlit):
        """
        Test error handling when token generator raises exception.
        Should catch exception, display error via st.error(), and return error string.
        """

        def failing_generator():
            yield "Partial"
            raise ValueError("Generator failed")

        result = render_stream(failing_generator())

        # Verify error displayed
        mock_streamlit.error.assert_called_once()
        error_msg = mock_streamlit.error.call_args[0][0]
        assert "Error during generation" in error_msg

        # Verify error string returned
        assert result == "Error generating response."

    def test_render_stream_special_characters(self, mock_streamlit):
        """Test render_stream with special characters and emoji."""
        token_generator = iter(["🌍 ", "African", " history", " is ", "✨ ", "rich"])

        result = render_stream(token_generator)

        assert result == "🌍 African history is ✨ rich"

    def test_render_stream_multiline_text(self, mock_streamlit):
        """Test render_stream with multiline text (newlines in tokens)."""
        token_generator = iter(["Line 1\n", "Line 2\n", "Line 3"])

        result = render_stream(token_generator)

        assert result == "Line 1\nLine 2\nLine 3"

    def test_render_stream_context_manager(self, mock_streamlit):
        """Test that render_stream uses st.chat_message as context manager."""
        token_generator = iter(["test"])

        render_stream(token_generator)

        # Verify chat_message was used as context manager
        mock_streamlit.chat_message.assert_called_once_with("assistant")
        # __enter__ and __exit__ should be called on the context manager
        assert mock_streamlit.chat_message.return_value.__enter__.called
        assert mock_streamlit.chat_message.return_value.__exit__.called

    def test_render_stream_markdown_updates_progressively(self, mock_streamlit):
        """
        Test that markdown is called progressively with accumulated tokens.
        Verifies that display updates in real-time as tokens arrive.
        """
        mock_container = mock_streamlit.empty.return_value
        mock_container.markdown = MagicMock()

        token_generator = iter(["A", "B", "C"])

        render_stream(token_generator)

        calls = mock_container.markdown.call_args_list
        # Progressive accumulation: "A▌", "AB▌", "ABC▌", then final "ABC"
        assert "A▌" in calls[0][0][0]
        assert "AB▌" in calls[1][0][0]
        assert "ABC▌" in calls[2][0][0]
        assert calls[3][0][0] == "ABC"
