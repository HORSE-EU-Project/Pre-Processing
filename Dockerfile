# Use an official Python runtime as a parent image
FROM python:3.9.12

# Set the working directory in the container
WORKDIR /dff

# Copy only the requirements.txt initially to leverage Docker cache
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip --no-cache-dir install -r requirements.txt

# Copy the rest of the application
COPY schema.sql user.py db.py app.py keycloak_requests.py ./
COPY ./Web_app ./Web_app
COPY ./templates ./templates
COPY ./static ./static

# Run app.py when the container launches
CMD ["python3", "-u", "app.py"]
