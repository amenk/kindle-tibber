# Use a Python base image
FROM python:3.11-slim

# Set the working directory inside the container
RUN mkdir /app
WORKDIR /app

# Install required packages for running the script
RUN apt-get update && apt-get install -y \
    cron \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script to the container
COPY script.py /app/script.py

# Create a cron job to run the script every minute
RUN echo "* * * * * python /app/script.py" > /etc/cron.d/tibber-cron

# Give execution permissions to the cron job
RUN chmod 0644 /etc/cron.d/tibber-cron

# Apply cron job
RUN crontab /etc/cron.d/tibber-cron

# Expose the port to serve the image
EXPOSE 8000

# Run the cron service and simple HTTP server
CMD python /app/script.py && cron && python3 -m http.server 8000 --bind 0.0.0.0

