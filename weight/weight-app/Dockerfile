FROM python:3.12-slim

WORKDIR /app

COPY weight-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY weight-app/db.py .
COPY weight-app/main.py .
COPY weight-app/mock_routes.py .
COPY weight-app/weight_service.py .
COPY weight-app/templates/ ./templates/
COPY weight-app/static/ ./static/
COPY tests/ ./tests/

EXPOSE 5000
CMD ["python", "main.py"]