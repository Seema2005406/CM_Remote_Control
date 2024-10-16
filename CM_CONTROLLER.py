import os
import time
import logging
from pycarmaker import CarMaker, Quantity  # CarMaker Library
from kuksa_client.grpc import VSSClient  # Kuksa Library

# Get the KUKSA data broker IP and port from environment variables
KUKSA_DATA_BROKER_IP = '20.79.188.178'  # Replace with your KUKSA server IP
KUKSA_DATA_BROKER_PORT = 55555  # Default port for KUKSA

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize CarMaker
carMaker_IP = "localhost"  # Change if necessary
carMaker_Port = 16660  # Default CarMaker port
cm = CarMaker(carMaker_IP, carMaker_Port)
cm.connect()

# Subscribe to necessary quantities in CarMaker
throttle_quantity = Quantity("Vehicle.OBD.RelativeThrottlePosition", Quantity.FLOAT)
brake_quantity = Quantity("Vehicle.Chassis.Brake.PedalPosition", Quantity.FLOAT)
steering_quantity = Quantity("Vehicle.Speed", Quantity.FLOAT)
handbrake_quantity = Quantity("Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear", Quantity.FLOAT)
reverse_quantity = Quantity("Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear", Quantity.FLOAT)
clutch_quantity = Quantity("Vehicle.Powertrain.Transmission.ClutchEngagement", Quantity.FLOAT)

# Subscribe to quantities
cm.subscribe(throttle_quantity)
cm.subscribe(brake_quantity)
cm.subscribe(steering_quantity)
cm.subscribe(handbrake_quantity)
cm.subscribe(reverse_quantity)
cm.subscribe(clutch_quantity)

def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

def map_kuksa_to_carmaker(updates):
    """Map the KUKSA signal values to the CarMaker control."""
    throttle = updates['Vehicle.OBD.RelativeThrottlePosition'].value
    brake = updates['Vehicle.Chassis.Brake.PedalPosition'].value
    steering = updates['Vehicle.Speed'].value
    handbrake = updates['Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear'].value
    reverse = updates['Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear'].value

    # Clamp throttle to a valid range
    throttle = clamp(throttle, -1.0, 1.0)

    # Send values to CarMaker
    cm.DVA_write(throttle_quantity, throttle)  # Set throttle
    cm.DVA_write(brake_quantity, brake)        # Set brake
    cm.DVA_write(handbrake_quantity, handbrake)  # Set handbrake
    cm.DVA_write(reverse_quantity, reverse)    # Set reverse
    cm.DVA_write(steering_quantity, steering)  # Set steering

    # Log the current state for debugging
    logging.info(f"Throttle: {throttle}, Brake: {brake}, Steering: {steering}, Handbrake: {handbrake}, Reverse: {reverse}")

def main():
    with VSSClient(KUKSA_DATA_BROKER_IP, KUKSA_DATA_BROKER_PORT) as client:
        # Subscribe to the signals published by the G29 controller script
        client.subscribe_current_values([
            'Vehicle.OBD.RelativeThrottlePosition',
            'Vehicle.Chassis.Brake.PedalPosition',
            'Vehicle.Speed',
            'Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear',
            'Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear',
            'Vehicle.Powertrain.Transmission.ClutchEngagement',
        ])

        print("Subscribed to KUKSA signals...")

        while True:
            # Get the current values for the subscribed signals
            updates = client.get_current_values([
                'Vehicle.OBD.RelativeThrottlePosition',
                'Vehicle.Chassis.Brake.PedalPosition',
                'Vehicle.Speed',
                'Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear',
                'Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear',
                'Vehicle.Powertrain.Transmission.ClutchEngagement',
            ])

            # Map the KUKSA signals to CarMaker control
            map_kuksa_to_carmaker(updates)

            # Print the current values for debugging
            print("Current Values:")
            print(f"Throttle: {updates['Vehicle.OBD.RelativeThrottlePosition'].value}")
            print(f"Brake: {updates['Vehicle.Chassis.Brake.PedalPosition'].value}")
            print(f"Steering: {updates['Vehicle.Speed'].value}")
            print(f"Handbrake Active: {updates['Vehicle.Chassis.Axle.Row1.Wheel.Right.Brake.PadWear'].value}")
            print(f"Reverse Active: {updates['Vehicle.Chassis.Axle.Row2.Wheel.Left.Brake.PadWear'].value}")
            print("----------------------------")

            time.sleep(0.1)  # Adjust the delay for a smooth control loop

if __name__ == '__main__':
    main()
