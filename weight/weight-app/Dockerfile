FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db.py .
COPY main.py .
COPY test_routes.py .


EXPOSE 5000
CMD ["python", "main.py"]