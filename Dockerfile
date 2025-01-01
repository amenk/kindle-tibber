# Use a Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install required packages for running the script and Flask
RUN apt-get update && apt-get install -y \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script to the container
COPY app.py /app/app.py

# Expose the port to serve the image
EXPOSE 8000

# Run the Flask app
CMD ["python3", "app.py"]

