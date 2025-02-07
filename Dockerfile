# Use a Python base image (e.g., Python 3.9)
FROM python:3.9-slim

# Set working directory in the container
WORKDIR /app

# Copy the requirements.txt to the working directory
COPY requirements.txt /app/

# Install the dependencies from the requirements.txt file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the .env file to the working directory
COPY .env /app/

# Copy the entire app folder contents into the container
COPY app /app/

# Set the environment variables from the .env file
# This automatically loads the variables inside the container for use in the application
ENV $(cat .env | xargs)

# Set the default command to run the application (main.py)
CMD ["python", "main.py"]
