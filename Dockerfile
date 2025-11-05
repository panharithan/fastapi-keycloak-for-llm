FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app/app

RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run both FastAPI and Gradio in parallel
CMD ["bash", "-c", "uvicorn app.app:app --host 0.0.0.0 --port 8000 & python app/ui.py"]
