import time
import threading
import pygame
import logging
from kuksa_client.grpc import VSSClient
from kuksa_client.grpc import Datapoint

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Joystick Reader Thread Class
class JoystickReader(threading.Thread):
    def __init__(self):
        super().__init__()
        # Initialize all values to 0
        self.steering = 0.0
        self.gas = 0.0
        self.brake = 0.0
        self.clutch = 0.0
        self.handbrake = 0
        self.reverse = 0
        self.enter = 0
        self.exit = 0
        self.user_input = 0.0  # Variable for new axis 6 input
        self.isRunning = True
        self.lock = threading.Lock()  # To make joystick data access thread-safe
        self.precisionDecimals = 3
        self.sleepTime = 0.1  # Shortened sleep time for more frequent updates

    def pedalValuesNormalize(self, val):
        # Normalize pedal values to a range of 0 to 1
        return round((1 - val) / 2, self.precisionDecimals)

    def steeringValuesNormalize(self, val):
        # Normalize steering values (scaling factor adjusted for demonstration)
        return round(val * 9, self.precisionDecimals)

    def run(self):
        pygame.init()
        pygame.joystick.init()

        try:
            # Initialize joystick (assuming G29 is the first joystick connected)
            joystick = pygame.joystick.Joystick(0)
            joystick.init()
            logging.info("Joystick initialized successfully.")
        except pygame.error as e:
            logging.error(f"Joystick initialization failed: {e}")
            self.isRunning = False
            return

        while self.isRunning:
            with self.lock:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.isRunning = False

                # Read joystick axis values
                _steering = joystick.get_axis(0)  # Axis 0 for steering wheel
                _brake = joystick.get_axis(3)     # Axis 3 for brake
                _clutch = joystick.get_axis(1)    # Axis 1 for clutch
                _gas = joystick.get_axis(2)       # Axis 2 for throttle/gas
                
                # Update joystick values
                self.steering = self.steeringValuesNormalize(_steering * -1)
                self.brake = self.pedalValuesNormalize(_brake)
                self.clutch = self.pedalValuesNormalize(_clutch)
                self.gas = self.pedalValuesNormalize(_gas)
                  # Normalizing axis 6 value

                # Button values
                self.handbrake = 1 if joystick.get_button(4) else 0
                self.reverse = 1 if joystick.get_button(5) else 0
                self.enter = 1 if joystick.get_button(6) else 0
                self.exit = 1 if joystick.get_button(7) else 0

            time.sleep(self.sleepTime)

    def stop(self):
        self.isRunning = False

# KUKSA Client Thread to send data
class ConnectToKuksa(threading.Thread):
    def __init__(self, joystick_reader):
        super().__init__()
        self.joystick_reader = joystick_reader
        self.isRunning = True
        self.retries = 0
        self.max_retries = 5  # Max retry attempts to reconnect
        self.first_run = True  # Flag to send initial zero values

    def run(self):
        kuksaDataBroker_IP = '20.79.188.178'
        kuksaDataBroker_Port = 55555

        while self.retries < self.max_retries:
            try:
                with VSSClient(kuksaDataBroker_IP, kuksaDataBroker_Port) as client:
                    logging.info(f"Connected to KUKSA Data Broker at {kuksaDataBroker_IP}:{kuksaDataBroker_Port}")

                    while self.isRunning and self.joystick_reader.isRunning:
                        with self.joystick_reader.lock:
                            if self.first_run:
                                # Send initial zero values to KUKSA
                                client.set_current_values({
                                    'Vehicle.OBD.RelativeThrottlePosition': Datapoint(0.0),
                                    'Vehicle.Powertrain.Transmission.ClutchEngagement': Datapoint(0.0),
                                    'Vehicle.ADAS.CruiseControl.SpeedSet': Datapoint(0.0),
                                    'Vehicle.Speed': Datapoint(0.0),
                                    'Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear': Datapoint(False),
                                    'Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear': Datapoint(False),
                                    'Vehicle.ADAS.CruiseControl.IsActive': Datapoint(False),
                                    'Vehicle.ADAS.CruiseControl.IsEnabled': Datapoint(False),
                                    
                                })
                                logging.info("Sent initial values: All zeros")
                                self.first_run = False
                            else:
                                # Send joystick values to KUKSA Data Broker
                                client.set_current_values({
                                    'Vehicle.OBD.RelativeThrottlePosition': Datapoint(float(self.joystick_reader.gas)),
                                    'Vehicle.Powertrain.Transmission.ClutchEngagement': Datapoint(float(self.joystick_reader.clutch)),
                                    'Vehicle.ADAS.CruiseControl.SpeedSet': Datapoint(float(self.joystick_reader.brake)),
                                    'Vehicle.Speed': Datapoint(float(self.joystick_reader.steering)),
                                    'Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear': Datapoint(bool(self.joystick_reader.handbrake)),
                                    'Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear': Datapoint(bool(self.joystick_reader.reverse)),
                                    'Vehicle.ADAS.CruiseControl.IsActive': Datapoint(bool(self.joystick_reader.enter)),
                                    'Vehicle.ADAS.CruiseControl.IsEnabled': Datapoint(bool(self.joystick_reader.exit)),
                                   
                                })

                                # Logging data for debugging
                                logging.info(f"Sent to KUKSA - Gas: {self.joystick_reader.gas}, "
                                             f"Clutch: {self.joystick_reader.clutch}, Brake: {self.joystick_reader.brake}, "
                                             f"Steering: {self.joystick_reader.steering}, Handbrake: {self.joystick_reader.handbrake}, "
                                             f"Reverse: {self.joystick_reader.reverse}, Enter: {self.joystick_reader.enter}, "
                                             f"Exit: {self.joystick_reader.exit}")
                        time.sleep(0.1)

            except Exception as e:
                logging.error(f"Connection error: {e}. Retrying ({self.retries}/{self.max_retries})...")
                self.retries += 1
                time.sleep(2)  # Wait before retrying the connection

        if self.retries >= self.max_retries:
            logging.critical("Max retries reached. Failed to reconnect to KUKSA Data Broker.")

    def stop(self):
        self.isRunning = False

# Main logic to run the threads
if __name__ == '__main__':
    joystick_reader = JoystickReader()
    kuksa_client = ConnectToKuksa(joystick_reader)

    joystick_reader.start()
    kuksa_client.start()

    try:
        while joystick_reader.isRunning and kuksa_client.isRunning:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt caught. Stopping threads...")
        joystick_reader.stop()
        joystick_reader.join()
        kuksa_client.stop()
        kuksa_client.join()
        print("Threads have been stopped.")
