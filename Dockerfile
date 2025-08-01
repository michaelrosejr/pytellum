# Use the official Python 3.13 base image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application's requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code into the container
COPY pytellum/. .

# Define the command to run the application
CMD ["python", "main.py"]