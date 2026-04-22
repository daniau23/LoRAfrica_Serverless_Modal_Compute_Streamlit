# **TESTS FOR LORAFRICA**

This folder serves as the testing plaform for Streamlit LoRAfrica to ensure new integrations works fine.

As new features are added, they will be tested

Current test success results can be found in `tests_results.md`. This will always be updated 

To run pytests use
Ensure requirements are installed

```bash
pytest -v
```
or

```bash
pytest --cov=services --cov=config --cov=utils --cov-report=html
```