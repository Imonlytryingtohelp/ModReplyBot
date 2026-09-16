# Dockerfile for building modreplybot image
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY config.py .
COPY modreplybot.py .
COPY update_checker.py .
COPY web web
ENV PYTHONUNBUFFERED=1
CMD ["python", "modreplybot.py"]
