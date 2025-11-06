FROM python:3.11-slim

WORKDIR /app

# Ensure Python finds the package
ENV PYTHONPATH=/app

# Install dependencies
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run both FastAPI (app.app:app) and Gradio (app.ui) in parallel
CMD ["bash", "-c", "uvicorn app.app:app --host 0.0.0.0 --port 8000 & python -m app.ui"]