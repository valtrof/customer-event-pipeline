FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY components/ ./components/
COPY pipeline.py .
COPY submit.py .

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python"]
