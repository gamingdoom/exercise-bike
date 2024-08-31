#!/usr/bin/env python3

# # Import driver from parent directory
# import sys
# import pathlib as path

# directory = path.Path(__file__).absolute().parent
# sys.path.append(directory)

from driver import ExerciseBike, ModeFlags, Results

bike = ExerciseBike(ModeFlags.NORMAL)

bike.start()

motor_lut = bike.get_motor_voltage_lut(50, True)
servo_lut = bike.get_servo_degrees_lut(60, True)

bike.close()

with open("motor_lut.csv", "w") as f:    
    f.write(motor_lut)

with open("servo_lut.csv", "w") as f:    
    f.write(servo_lut)
