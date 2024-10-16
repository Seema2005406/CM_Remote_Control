
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install necessary system dependencies
RUN apt-get update && \
    apt-get install -y \
    git \
    build-essential \
    python3-dev \
    python3-pip \
    libffi-dev \
    libssl-dev \
    i2c-tools \
    python3-smbus \
    python3-pil \
    && apt-get clean

# Install required Python packages
RUN pip install --no-cache-dir kuksa-client protobuf traitlets adafruit-blinka adafruit-circuitpytho$

# Install jetracer from the official GitHub repository
RUN pip install --no-cache-dir git+https://github.com/NVIDIA-AI-IOT/jetracer.git

# Expose the KUKSA port
EXPOSE ${KUKSA_DATA_BROKER_PORT}

# Run the application when the container launches
CMD ["python", "./car_controller.py"]

