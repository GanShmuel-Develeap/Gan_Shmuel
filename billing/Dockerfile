# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app
# ENV FLASK_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0
# Copy the requirements file first to leverage Docker cache
# Make sure you have a requirements.txt with: flask, flask-sqlalchemy, pymysql
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
# This includes app.py, routes.py, and utils.py
COPY . .



# Expose the port Flask runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
# CMD ["flask", "run", "--debug"]
