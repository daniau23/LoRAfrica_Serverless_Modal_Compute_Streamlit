# **TESTS RESULTS**

```bash
pytest --cov=services --cov=config --cov=utils --cov-report=html
================================================= test session starts =================================================
platform win32 -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- 
~\python.exe
cachedir: .pytest_cache
rootdir: ~streamlit
configfile: pytest.ini
plugins: anyio-4.12.1, langsmith-0.3.42, cov-7.1.0, mock-3.14.1
collected 60 items

config\test_settings.py::TestSettingsModule::test_max_tokens_constant PASSED                                     [  1%]
config\test_settings.py::TestSettingsModule::test_temperature_constant PASSED                                    [  3%]
config\test_settings.py::TestSettingsModule::test_settings_constants_types PASSED                                [  5%]
config\test_settings.py::TestSettingsModule::test_settings_constants_values_reasonable PASSED                    [  6%]
integration\test_generation_flow.py::TestGenerationFlow::test_generation_flow_end_to_end PASSED                  [  8%]
integration\test_generation_flow.py::TestGenerationFlow::test_generation_flow_with_temperature_override PASSED   [ 10%]
integration\test_generation_flow.py::TestGenerationFlow::test_generation_flow_streaming_tokens_displayed PASSED  [ 11%]
integration\test_generation_flow.py::TestGenerationFlow::test_generation_flow_error_handling PASSED              [ 13%]
integration\test_generation_flow.py::TestGenerationFlow::test_generation_flow_no_lora_model PASSED               [ 15%]
integration\test_generation_flow.py::TestGenerationFlow::test_generation_flow_with_malformed_json PASSED         [ 16%]
integration\test_generation_flow.py::TestRegenerationFlow::test_regeneration_flow_creates_new_response PASSED    [ 18%]
integration\test_generation_flow.py::TestRegenerationFlow::test_regeneration_flow_uuid_persistence PASSED        [ 20%]
integration\test_generation_flow.py::TestRegenerationFlow::test_regeneration_flow_temp_override PASSED           [ 21%]
integration\test_generation_flow.py::TestRegenerationFlow::test_regeneration_flow_always_uses_lora PASSED        [ 23%]
integration\test_generation_flow.py::TestRegenerationFlow::test_regeneration_flow_flags_correctly_set PASSED     [ 25%]
services\test_generation.py::TestGenerateResponse::test_generate_response_success_with_lora PASSED               [ 26%]
services\test_generation.py::TestGenerateResponse::test_generate_response_without_lora PASSED                    [ 28%]
services\test_generation.py::TestGenerateResponse::test_generate_response_with_temp_override PASSED              [ 30%]
services\test_generation.py::TestGenerateResponse::test_generate_response_with_regeneration_flags PASSED         [ 31%]
services\test_generation.py::TestGenerateResponse::test_generate_response_exception_handling PASSED              [ 33%]
services\test_generation.py::TestGenerateResponse::test_handle_regeneration_calls_generate_response PASSED       [ 35%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_basic PASSED                          [ 36%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_payload_structure PASSED              [ 38%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_default_temperature PASSED            [ 40%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_with_regeneration_flags PASSED        [ 41%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_api_error PASSED                      [ 43%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_empty_lines_skipped PASSED            [ 45%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_malformed_json_skipped PASSED         [ 46%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_done_signal_stops_iteration PASSED    [ 48%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_missing_content_field PASSED          [ 50%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_url_from_settings PASSED              [ 51%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_streaming_enabled PASSED              [ 53%]
services\test_generation_core.py::TestStreamResponse::test_stream_response_complex_payload PASSED                [ 55%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_accumulates_tokens PASSED                   [ 56%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_displays_typing_indicator PASSED            [ 58%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_removes_typing_indicator_at_end PASSED      [ 60%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_creates_chat_message PASSED                 [ 61%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_empty_generator PASSED                      [ 63%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_single_token PASSED                         [ 65%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_long_response PASSED                        [ 66%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_exception_in_generator PASSED               [ 68%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_special_characters PASSED                   [ 70%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_multiline_text PASSED                       [ 71%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_context_manager PASSED                      [ 73%]
services\test_generation_ui.py::TestRenderStream::test_render_stream_markdown_updates_progressively PASSED       [ 75%]
services\test_regeneration.py::TestHandleRegeneration::test_handle_regeneration_creates_regen_id_if_none PASSED  [ 76%]
services\test_regeneration.py::TestHandleRegeneration::test_handle_regeneration_preserves_existing_regen_id PASSED [ 78%]
services\test_regeneration.py::TestHandleRegeneration::test_handle_regeneration_increments_regen_index PASSED    [ 80%]
services\test_regeneration.py::TestHandleRegeneration::test_handle_regeneration_calls_generate_response PASSED   [ 81%]
services\test_regeneration.py::TestHandleRegeneration::test_handle_regeneration_returns_new_response PASSED      [ 83%]
services\test_regeneration.py::TestHandleRegeneration::test_handle_regeneration_uses_override_temp PASSED        [ 85%]
services\test_regeneration.py::TestHandleRegeneration::test_handle_regeneration_always_uses_lora PASSED          [ 86%]
utils\test_constants.py::TestConstants::test_app_title_constant PASSED                                           [ 88%]
utils\test_constants.py::TestConstants::test_chat_input_placeholder_constant PASSED                              [ 90%]
utils\test_constants.py::TestConstants::test_default_regen_temp_constant PASSED                                  [ 91%]
utils\test_constants.py::TestConstants::test_default_regen_temp_higher_than_base PASSED                          [ 93%]
utils\test_constants.py::TestConstants::test_app_title_contains_emoji PASSED                                     [ 95%]
utils\test_constants.py::TestConstants::test_constants_are_strings PASSED                                        [ 96%]
utils\test_constants.py::TestConstants::test_chat_placeholder_mentions_model_name PASSED                         [ 98%]
utils\test_constants.py::TestConstants::test_constants_non_empty PASSED                                          [100%]

=================================================== tests coverage ====================================================
__________________________________ coverage: platform win32, python 3.11.14-final-0 ___________________________________

Coverage HTML written to dir htmlcov
================================================= 60 passed in 8.72s ==================================================
```