# Dockerfile

# Use -slim for a lighter version of python docker image
FROM python:3.8-slim

# Set environment variables from .env
ARG DATABASE_URL
ARG API_KEY
ARG SECRET_KEY
ARG DB_HOST
ARG DB_USER
ARG DB_PASSWORD
ARG DB_NAME

ENV DATABASE_URL=${DATABASE_URL}
ENV API_KEY=${API_KEY}
ENV SECRET_KEY=${SECRET_KEY}
ENV DB_HOST=${DB_HOST}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}
ENV DB_NAME=${DB_NAME}

# Install dependencies
COPY requirements.txt .

# Update pip to the latest version
RUN pip install --upgrade pip

RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Run the application
CMD ["python", "app.py"]



