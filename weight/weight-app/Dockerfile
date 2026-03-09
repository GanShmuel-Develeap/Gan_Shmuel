FROM python:3.12-slim

WORKDIR /app

COPY weight-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db.py .
COPY main.py .
COPY mock_routes.py .
COPY weight_service.py .
COPY templates/ ./templates/
COPY static/ ./static/
COPY weight-app/db.py .
COPY weight-app/main.py .
COPY weight-app/mock_routes.py .
COPY tests/ ./tests

EXPOSE 5000
CMD ["python", "main.py"]