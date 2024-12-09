# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install MQTT client library and other dependencies
RUN pip install paho-mqtt setuptools

# Download and install xled library
RUN curl -L https://github.com/scrool/xled/archive/refs/tags/v0.7.0.tar.gz -o xled.tar.gz \
    && tar -xzf xled.tar.gz \
    && cd xled-0.7.0 \
    && python setup.py install \
    && cd .. \
    && rm -rf xled.tar.gz xled-0.7.0

# Copy the Python script into the container
COPY monitor.py /app/monitor.py

# Set the default command to run the script
CMD ["python", "/app/monitor.py"]