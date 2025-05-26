# Start with a Python base image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code into the container
COPY ./app /app

# Copy the .env file into the container
COPY .env /app/.env

# Set the environment variable to specify the Python path
ENV PYTHONPATH=/app

# Command to run the application
CMD ["python", "main.py"]
