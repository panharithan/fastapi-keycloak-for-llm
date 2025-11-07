
```
tests/
├── __init__.py
├── conftest.py
├── test_app.py               # General API tests
├── test_auth.py              # Secure + token-based endpoints
├── test_verification.py      # Email and resend verification
└── test_llm.py               # LLM-related endpoint
```
Test with coverage (run from root folder)
```
pytest --cov=app --cov-report=term-missing -v
```

Save reports
```
pytest tests --cov=app --cov-report=term-missing -v > tests/pytest_report.txt 2>&1
```
•	> test_report.txt redirects standard output (stdout) to the file.
•	2>&1 redirects standard error (stderr) to the same file, so you get all logs.