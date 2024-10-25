import os
import time
import logging
import threading
from pycarmaker import CarMaker, Quantity  # CarMaker Library
from kuksa_client.grpc import VSSClient  # Kuksa Library

# Get the KUKSA data broker IP and port
KUKSA_DATA_BROKER_IP = '20.79.188.178'  # Replace with your KUKSA server IP
KUKSA_DATA_BROKER_PORT = 55555  # Default port for KUKSA

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Event to control when writing to CarMaker starts
simulation_ready_event = threading.Event()

class CarMakerController(threading.Thread):
    def __init__(self):
        super().__init__()
        self.carMaker_IP = "localhost"
        self.carMaker_Port = 16660
        self.cm = CarMaker(self.carMaker_IP, self.carMaker_Port)
        self.is_running = True

        # Subscribe to CarMaker quantities
        self.throttle_quantity = Quantity("DM.Gas", Quantity.FLOAT)
        self.brake_quantity = Quantity("DM.Brake", Quantity.FLOAT)
        self.steering_quantity = Quantity("DM.Steer.Ang", Quantity.FLOAT)
        self.clutch_quantity = Quantity("DM.Clutch", Quantity.FLOAT)
        self.handbrake_quantity = Quantity("DM.Handbrake", Quantity.FLOAT)
        self.user_out_quantity = Quantity("UserOut_01", Quantity.FLOAT)  # User output quantity

        self.cm.connect()
        self.cm.subscribe(self.throttle_quantity)
        self.cm.subscribe(self.brake_quantity)
        self.cm.subscribe(self.steering_quantity)
        self.cm.subscribe(self.clutch_quantity)
        self.cm.subscribe(self.handbrake_quantity)
        self.cm.subscribe(self.user_out_quantity)  # Subscribe to user output

    def run(self):
        # Start CarMaker simulation and wait for it to be ready
        print(self.cm.send("::Cockpit::Close\r"))
        print(self.cm.send("::Cockpit::Popup\r"))
        print(self.cm.send("StartSim\r"))
        print(self.cm.send("WaitForStatus running\r"))  # Wait until CarMaker simulation is running

        simulation_ready_event.set()  # Signal that the simulation is ready for data writing
        logging.info("CarMaker simulation is running. Ready to write data.")

        while self.is_running:
            time.sleep(0.2)  # Keep the thread alive

    def write_values(self, throttle, brake, steering, clutch, handbrake, reverse):
        """Write KUKSA values to CarMaker."""
        print(self.cm.DVA_write(self.throttle_quantity, throttle))  # Set throttle
        print(self.cm.DVA_write(self.brake_quantity, brake))        # Set brake
        print(self.cm.DVA_write(self.steering_quantity, steering))  # Set steering
        print(self.cm.DVA_write(self.clutch_quantity, clutch))  
        print(self.cm.DVA_write(self.handbrake_quantity, handbrake))

    def stop(self):
        self.is_running = False

class KuksaReader(threading.Thread):
    def __init__(self, car_maker_controller):
        super().__init__()
        self.car_maker_controller = car_maker_controller
        self.is_running = True
        self.should_write = False  # Flag to control writing
        self.user_out_count = 0  # Counter for UserOut_01 encounters

    def run(self):
        with VSSClient(KUKSA_DATA_BROKER_IP, KUKSA_DATA_BROKER_PORT) as client:
            # Subscribe to KUKSA signals
            client.subscribe_current_values([
                'Vehicle.OBD.RelativeThrottlePosition',
                'Vehicle.ADAS.CruiseControl.SpeedSet',
                'Vehicle.Speed',
                'Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear',
                'Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear',
                'Vehicle.Powertrain.Transmission.ClutchEngagement',
            ])
            print("Subscribed to KUKSA signals...")

            # Wait for CarMaker to be ready
            simulation_ready_event.wait()  # Wait for the CarMaker simulation to be running
            time.sleep(1)
            while self.is_running:
                # Get the current values for the subscribed signals
                updates = client.get_current_values([
                    'Vehicle.OBD.RelativeThrottlePosition',
                    'Vehicle.ADAS.CruiseControl.SpeedSet',
                    'Vehicle.Speed',
                    'Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear',
                    'Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear',
                    'Vehicle.Powertrain.Transmission.ClutchEngagement',
                ])

                # Map and send KUKSA signals to CarMaker
                throttle = updates['Vehicle.OBD.RelativeThrottlePosition'].value
                brake = updates['Vehicle.ADAS.CruiseControl.SpeedSet'].value
                steering = updates['Vehicle.Speed'].value
                clutch = updates['Vehicle.Powertrain.Transmission.ClutchEngagement'].value
                handbrake = updates['Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear'].value
                reverse = updates['Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear'].value

                # Check the value of UserOut_01
                user_out_value = self.car_maker_controller.cm.DVA_read(self.car_maker_controller.user_out_quantity)

                # Check for UserOut_01 encounters
                if user_out_value == 1.0:
                    self.user_out_count += 1  # Increment count if 1.0 is encountered

                # Start writing on the first encounter of 1.0
                if self.user_out_count == 1:
                    self.should_write = True
                    logging.info("Writing has started.")

                # Stop writing on the second encounter of 1.0
                if self.user_out_count == 2:
                    self.should_write = False
                    logging.info("Writing has stopped.")

                # Write values if should_write is True
                if self.should_write:
                    self.car_maker_controller.write_values(throttle, brake, steering, clutch, handbrake, reverse)
                    logging.info(f"Throttle: {throttle}, Brake: {brake}, Steering: {steering}, Clutch: {clutch}, Handbrake: {handbrake}, Reverse/Gear: {reverse}")

                time.sleep(0.1)  # Adjust delay for smooth control loop

    def stop(self):
        self.is_running = False

if __name__ == '__main__':
    car_maker_controller = CarMakerController()
    kuksa_reader = KuksaReader(car_maker_controller)

    car_maker_controller.start()  # Start CarMaker thread
    kuksa_reader.start()  # Start KUKSA reader thread

    try:
        while True:
            time.sleep(0.1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt caught. Stopping threads...")
        car_maker_controller.stop()
        kuksa_reader.stop()
        car_maker_controller.join()
        kuksa_reader.join()
        print("Threads have been stopped.")
