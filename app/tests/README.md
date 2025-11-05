tests/
├── __init__.py
├── conftest.py
├── test_app.py               # General API tests
├── test_auth.py              # Secure + token-based endpoints
├── test_verification.py      # Email and resend verification
└── test_llm.py               # LLM-related endpoint

Test with coveraage
$ pytest --cov=app --cov-report=term-missing -v