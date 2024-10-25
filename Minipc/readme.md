# G29 Controller with KUKSA Data Broker Integration

## Overview

This project enables the use of the Logitech G29 steering wheel controller for automotive simulation and real-time vehicle data integration. The steering wheel's input values are sent to a KUKSA Data Broker, an open-source platform for handling vehicle data, through the `kuksa-client`. The program reads inputs like throttle, clutch, brake, and steering from the G29 and sends them as data points to KUKSA.

### Features
- Reads G29 steering wheel controller inputs.
- Sends data such as throttle, clutch, brake, steering, handbrake, and more to the KUKSA Data Broker.
- Provides a real-time stream of G29 controller values.

---

## Prerequisites

Before starting, ensure you have the following installed on your machine:

- **Docker**: You can install Docker from [here](https://docs.docker.com/get-docker/).
- **Logitech G29 Steering Wheel Controller** connected to your machine.

---

## Project Structure

- **`pub2.py`**: The main Python file that contains the logic for reading the G29 input and sending data to the KUKSA Data Broker.
- **`Dockerfile`**: The Docker configuration file that sets up the environment to run the Python application.

### `pub2.py`

This is the main Python script that:
1. Initializes the G29 steering wheel using `pygame`.
2. Reads various control inputs like throttle, clutch, brake, and steering.
3. Sends these values to the KUKSA Data Broker using the `kuksa-client`.

### `Dockerfile`

This Dockerfile creates a containerized environment with the necessary dependencies to run the `g29_kuksa.py` script. It installs Python, Pygame, and the KUKSA client for communication with the KUKSA Data Broker.


### Installation and Setup
1. Clone the Repository

Clone this repository to your local machine using:

```bash

git clone https://github.com/Seema2005406/CM_Remote_Control.git
```


2. Build the Docker Image

Build the Docker image using the provided Dockerfile:


```bash
docker build -t pygame-app .
```

3. Run the Docker Container

Run the Docker container:


```bash
docker run --rm -it \
  --privileged \
  --env=XDG_RUNTIME_DIR=/tmp/runtime-root \
  --device /dev/input/js0 \
  --device /dev/input/event0 \
  --device /dev/input/event1 \
  --device /dev/input/event2 \
  --device /dev/input/event3 \
  --device /dev/input/event4 \
  --device /dev/snd:/dev/snd \
  pygame-app
```
Explanation of the Command:

    --privileged: This flag allows the container to access hardware devices like joysticks and sound devices.
    --env=XDG_RUNTIME_DIR=/tmp/runtime-root: Sets the environment variable for XDG runtime, which is required for some SDL (Simple DirectMedia Layer) operations.
    --device /dev/input/js0: Grants access to the joystick device.
    --device /dev/input/event*: Allows access to the necessary event devices associated with the joystick.
    --device /dev/snd:/dev/snd: Provides access to the sound devices.

### Verifying the Joystick Connection

Before running the program, you can verify that your joystick is correctly connected using jstest on the host machine. To do this:

    Install jstest:

```bash

sudo apt install joystick
```

Run jstest to test the joystick input:

```bash

    jstest /dev/input/js0
```

### Using the Application

Once the Docker container is running, the application will automatically start reading input from the G29 controller and sending it to the KUKSA Data Broker. The following input mappings are used:

    Steering Wheel: Axis 0
    Clutch: Axis 1
    Throttle: Axis 2
    Brake: Axis 3
    Handbrake: Button 4
    Reverse: Button 5
    Enter: Button 6
    Exit: Button 7

You can monitor the values being sent to KUKSA in the terminal.
Dependencies

### The following dependencies are used in this project:

    Python 3.9 (from python:3.9-slim Docker image)
    Pygame for joystick handling
    KUKSA client for communication with the KUKSA Data Broker

All dependencies will be installed automatically when building the Docker image.

###Configuration

The IP address and port of the KUKSA Data Broker can be configured in the g29_kuksa.py script under the thread_ConnectToKuksa() function:


kuksaDataBroker_IP = '20.79.188.178'
kuksaDataBroker_Port = 55555

Modify these values based on your KUKSA Data Broker setup.

### Troubleshooting

No Joystick Detected: Ensure that the G29 steering wheel is connected properly to your machine. You can check if the joystick is recognized using the following Python code snippet:
```bash
import pygame
pygame.init()
print(pygame.joystick.get_count())
```
KUKSA Connection Issues: Verify that the KUKSA Data Broker is running and reachable from your network.

Privileged Mode in Docker: The application requires access to hardware (G29 controller), so ensure that you run the Docker container with the --privileged flag.
