FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db.py .
COPY main.py .
COPY test_routes.py .
COPY weight_service.py .
COPY templates/ ./templates/
COPY static/ ./static/


EXPOSE 5000
CMD ["python", "main.py"]