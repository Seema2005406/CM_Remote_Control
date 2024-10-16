# CarMaker KUKSA Integration

## Overview

This project demonstrates how to integrate the CarMaker simulation environment with KUKSA data broker to control a virtual vehicle's behavior. It utilizes the CarMaker API to read and write vehicle parameters based on real-time updates received from the KUKSA data broker. This integration allows for the simulation of vehicle dynamics in a controlled environment.

## Requirements

- **Python 3.6 or later**
- **Libraries**:
  - `pycarmaker` for interacting with CarMaker
  - `kuksa-client` for communication with the KUKSA data broker
- **CarMaker**: Ensure you have access to the CarMaker software and have it set up on your local machine or server.
- **KUKSA Data Broker**: A KUKSA server must be running and accessible.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/carmaker-kuksa-integration.git
   cd carmaker-kuksa-integration
Install the required Python packages:

bash
Copy code
pip install pycarmaker kuksa-client
Ensure CarMaker and KUKSA Data Broker are running:

Start the CarMaker simulation environment.
Start the KUKSA data broker on the specified IP and port.
Configuration
Before running the script, configure the following parameters:

Update the KUKSA server IP and port in the script:

python
Copy code
KUKSA_DATA_BROKER_IP = '20.79.188.178'  # Replace with your KUKSA server IP
KUKSA_DATA_BROKER_PORT = 55555  # Default port for KUKSA
Update the CarMaker connection parameters if necessary:

python
Copy code
carMaker_IP = "localhost"  # Change if CarMaker is on a different machine
carMaker_Port = 16660  # Default CarMaker port
Usage
Run the script:

bash
Copy code
python carmaker_kuksa_integration.py
The script will:

Connect to the KUKSA data broker and subscribe to relevant signals.
Connect to the CarMaker simulation environment.
Continuously read vehicle parameters from KUKSA and write them to CarMaker.
Monitor the output in the console for the current values of throttle, brake, steering, and other vehicle parameters.

Functionality
The script reads the following signals from the KUKSA data broker:

Vehicle throttle position
Brake pedal position
Vehicle speed
Handbrake status
Reverse status
Clutch engagement
It maps these values to the corresponding parameters in CarMaker to control the vehicle simulation.

Troubleshooting
Ensure that both CarMaker and KUKSA are running and that you can access them from the machine running the script.
Check for any connectivity issues or incorrect IP/port configurations.
Review the logging output for any error messages or warnings.
License
This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgements
CarMaker for providing the vehicle simulation environment.
KUKSA for offering a data broker that enables vehicle data communication.
markdown
Copy code

### Instructions for Use
1. **Clone and Configure**: Users should clone the repository and update the IP addresses and ports as necessary.
2. **Run the Script**: Provide clear instructions on how to execute the script.
3. **Monitor Output**: Encourage users to observe the console output to understand vehicle dynamics.
