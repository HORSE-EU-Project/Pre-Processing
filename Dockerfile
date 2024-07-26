# Dockerfile

# Use -slim for a lighter version of python docker image
FROM python:3.8-slim

# Install dependencies
COPY requirements.txt .

# Update pip to the latest version
RUN pip install --upgrade pip

RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Run the application
CMD ["python", "app.py"]



