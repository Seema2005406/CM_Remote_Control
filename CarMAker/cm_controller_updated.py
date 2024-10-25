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
try:
    cm = CarMaker(carMaker_IP, carMaker_Port)
    cm.connect()
    print("Connected to CarMaker")
except Exception as e:
    print(f"Failed to connect to CarMaker: {e}")

# Subscribe to necessary quantities in CarMaker
throttle_quantity = Quantity("DM.gas", Quantity.FLOAT)
brake_quantity = Quantity("DM.brake", Quantity.FLOAT)
steering_quantity = Quantity("DM.Steer.Ang", Quantity.FLOAT)
handbrake_quantity = Quantity("DM.Handbrake", Quantity.FLOAT)
clutch_quantity = Quantity("DM.Clutch", Quantity.FLOAT)

# Subscribe to quantities
cm.subscribe(throttle_quantity)
cm.subscribe(brake_quantity)
cm.subscribe(steering_quantity)
cm.subscribe(handbrake_quantity)
cm.subscribe(clutch_quantity)

def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

# Initialize ABS activation flag
abs_is_engaged = False  # This will toggle on the first encounter of ABS.IsEngaged == 1

def map_kuksa_to_carmaker(updates):
    """Map the KUKSA signal values to the CarMaker control."""
    global abs_is_engaged

    # Check ABS signal first
    signal = updates['Vehicle.ADAS.CruiseControl.IsActive'].value
    if signal == 1:
        abs_is_engaged = True

    # Only execute DVA_write if ABS has been set to 1 at least once
    if abs_is_engaged:
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
            'Vehicle.ADAS.CruiseControl.IsActive',  # ABS signal for control
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
                'Vehicle.ADAS.CruiseControl.IsActive',  # Get ABS engagement status
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
            print(f"Input: {updates['Vehicle.ADAS.CruiseControl.IsActive'].value}")
            print("----------------------------")

            time.sleep(0.1)  # Adjust the delay for a smooth control loop

if __name__ == '__main__':
    main()

