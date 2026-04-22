"""Unit tests for utils.constants module."""

import pytest


class TestConstants:
    """Tests for constants defined in utils.constants."""

    def test_app_title_constant(self):
        """Test that APP_TITLE is defined and non-empty."""
        from utils.constants import APP_TITLE

        assert APP_TITLE == "🌍 LoRAfrica - African History Assistant"
        assert isinstance(APP_TITLE, str)
        assert len(APP_TITLE) > 0

    def test_chat_input_placeholder_constant(self):
        """Test that CHAT_INPUT_PLACEHOLDER is defined and non-empty."""
        from utils.constants import CHAT_INPUT_PLACEHOLDER

        assert CHAT_INPUT_PLACEHOLDER == "I'm LoRAfrica, your African History Expert..."
        assert isinstance(CHAT_INPUT_PLACEHOLDER, str)
        assert len(CHAT_INPUT_PLACEHOLDER) > 0

    def test_default_regen_temp_constant(self):
        """Test that DEFAULT_REGEN_TEMP is defined and has correct value."""
        from utils.constants import DEFAULT_REGEN_TEMP

        assert DEFAULT_REGEN_TEMP == 0.3
        assert isinstance(DEFAULT_REGEN_TEMP, float)
        assert 0 <= DEFAULT_REGEN_TEMP <= 2

    def test_default_regen_temp_higher_than_base(self):
        """
        Test that DEFAULT_REGEN_TEMP is higher than base TEMPERATURE.
        Regeneration should introduce more variation than base generation.
        """
        from utils.constants import DEFAULT_REGEN_TEMP
        from config.settings import TEMPERATURE

        assert DEFAULT_REGEN_TEMP > TEMPERATURE

    def test_app_title_contains_emoji(self):
        """Test that APP_TITLE contains emoji for visual appeal."""
        from utils.constants import APP_TITLE

        # Contains globe emoji
        assert "🌍" in APP_TITLE
        assert "LoRAfrica" in APP_TITLE

    def test_constants_are_strings(self):
        """Test that text constants are strings."""
        from utils.constants import APP_TITLE, CHAT_INPUT_PLACEHOLDER

        assert isinstance(APP_TITLE, str)
        assert isinstance(CHAT_INPUT_PLACEHOLDER, str)

    def test_chat_placeholder_mentions_model_name(self):
        """Test that chat placeholder mentions the model name."""
        from utils.constants import CHAT_INPUT_PLACEHOLDER

        assert "LoRAfrica" in CHAT_INPUT_PLACEHOLDER

    def test_constants_non_empty(self):
        """Test that all string constants are non-empty."""
        from utils.constants import APP_TITLE, CHAT_INPUT_PLACEHOLDER

        assert len(APP_TITLE) > 0
        assert len(CHAT_INPUT_PLACEHOLDER) > 0
