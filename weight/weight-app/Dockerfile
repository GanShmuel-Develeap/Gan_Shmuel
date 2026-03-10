FROM python:3.12-slim

WORKDIR /app

COPY weight-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY weight-app/ .
COPY tests/ ./tests

EXPOSE 5000
CMD ["python", "main.py"]