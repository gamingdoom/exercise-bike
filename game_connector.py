#!/usr/bin/python
import socket
import struct
import math
import time

from driver.driver import ExerciseBike, ModeFlags, Results

GRAVITY = 9.81
ROLLING_RESISTANCE_COEFFICIENT = 0.01
BIKE_AND_RIDER_MASS = 75
AIR_DENSITY = 1.225
BIKE_AND_RIDER_AREA = 0.5
DRAG_COEFFICIENT = 1.0

DEBUG = True

def main():
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('0.0.0.0', 33356))

    if not DEBUG:
        # Connect to bike
        bike = ExerciseBike(ModeFlags.NORMAL)
        bike.start()
        print("Connected to bike!")

        velocity = bike.get_wheel_velocity()
    else:
        velocity = 5.0
        old_time = time.time()

    while True:
        # Read angle from client
        data, addr = server_socket.recvfrom(1024)
        angle = (struct.unpack("f", data)[0])

        # Get gravitational force
        newtons = GRAVITY * math.sin(math.radians(angle)) * BIKE_AND_RIDER_MASS

        # Calculate rolling resistance
        newtons += ROLLING_RESISTANCE_COEFFICIENT * GRAVITY * BIKE_AND_RIDER_MASS * math.cos(math.radians(angle))

        # Calculate drag
        newtons += 1/2 * DRAG_COEFFICIENT * AIR_DENSITY * BIKE_AND_RIDER_AREA * velocity * velocity

        accel = -newtons / BIKE_AND_RIDER_MASS

        # Calculate velocity
        if DEBUG:
            velocity += accel * (time.time() - old_time)

            if velocity < 0:
                velocity = 0
        else:
            if (r := bike.set_acceleration(accel)) != Results.SUCCESS:
                print("Failed to set acceleration")
                if r == Results.MOTOR_VOLTAGE_LUT_MISSING or r == Results.SERVO_DEGREES_LUT_MISSING:
                    print("LUT is missing! Please run driver/generate_luts.py")

            velocity = bike.get_wheel_velocity()

        if DEBUG:
            old_time = time.time()

        # Send velocity to client
        server_socket.sendto(struct.pack("f", velocity), addr)

        if DEBUG:
            print(f"Received angle: {angle}")
            print(f"Newtons: {newtons}")
            print(f"Acceleration: {accel}")
            print(f"Velocity: {velocity}")

    # Close client connection
    server_socket.close()

    # Close bike
    if not DEBUG:
        bike.close()

if __name__ == "__main__":
    main()