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
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install MQTT client library and other dependencies
RUN pip install paho-mqtt setuptools

# Download and install xled library
COPY xled-develop.zip /tmp/xled-develop.zip
RUN cd /tmp && \
    unzip xled-develop.zip && \
    cd xled-develop && \
    python setup.py install && \
    cd .. && \
    rm -rf xled-develop.zip xled-develop

# Copy the Python script into the container
COPY monitor.py /app/monitor.py

# Set the default command to run the script
CMD ["python", "/app/monitor.py"]