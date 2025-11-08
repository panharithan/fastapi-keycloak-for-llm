FROM python:3.11-slim

WORKDIR /app

# Ensure Python finds the package
ENV PYTHONPATH=/app

# Install dependencies
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


# 1. Run pytest (fail fast on any error)
# 2. If tests pass, run FastAPI and Gradio in parallel
CMD ["bash", "-c", "pytest app/tests --maxfail=1 --disable-warnings -q && uvicorn app.app:app --host 0.0.0.0 --port 8000 & python -m app.ui"]
