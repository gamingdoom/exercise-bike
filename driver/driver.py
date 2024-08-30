from enum import Enum
from multiprocessing import Process, Lock
import time
import struct
import serial

class ModeFlags(Enum):
    NORMAL = 0x00
    VIRTUAL_CONTROLLER = 0x01

class Results(Enum):
    SUCCESS = 0x00
    UNSPECIFIED_ERROR = 0x01
    CONNECTION_ALREADY_ESTABLISHED = 0x02
    BAD_MODE_FLAGS = 0x03
    INPUT_OUT_OF_RANGE = 0x04
    MOTOR_VOLTAGE_LUT_MISSING = 0x05
    SERVO_DEGREES_LUT_MISSING = 0x06

class Opcodes(Enum):
    START = 0x01
    KEEP_ALIVE = 0x02
    STOP = 0x03
    GET_WHEEL_VELOCITY = 0x04
    SET_MOTOR_VOLTAGE = 0x05
    SET_SERVO_DEGREES = 0x06
    GET_MOTOR_VOLTAGE_LUT = 0x07
    GET_SERVO_DEGREES_LUT = 0x08
    SET_ACCELERATION = 0x09
    SET_HID_CONTROLLER = 0x0A
    EMERGENCY_STOP = 0x0C

class ExerciseBike:
    def __init__(self, mode_flags: int, serial_port: str = "/dev/ttyACM0", baud_rate: int = 115200):
        self.mode_flags = mode_flags
        self.serial_port = serial_port
        self.baud_rate = baud_rate
    
    def start(self):
        # Connect via serial
        self.arduino = serial.Serial(self.serial_port, self.baud_rate)

        # Send start message
        self._send_opcode(Opcodes.START)
        self._send(struct.pack("B", self.mode_flags))

        # Receive start message
        if self._recv_result() != Results.SUCCESS:
            raise Exception("Failed to connect to bike!")
        
        # Launch thread that keeps connection alive
        self.comms_lock = Lock()
        self.keep_alive_thread = Process(target=self._keep_alive)
        self.keep_alive_thread.start()
        
    def close(self):
        self.keep_alive_thread.terminate()
        self._send_opcode(Opcodes.STOP)
        res = self._recv_result()
        self.arduino.close()

        return res
        
    def get_wheel_velocity(self) -> float:
        self._send_opcode(Opcodes.GET_WHEEL_VELOCITY)
        return struct.unpack("f", self._recv(4))[0]
    
    def set_motor_voltage(self, voltage: float):
        self._send_opcode(Opcodes.SET_MOTOR_VOLTAGE)
        self._send(struct.pack("f", voltage))

        return self._recv_result()
        
    def set_servo_degrees(self, degrees: float):
        self._send_opcode(Opcodes.SET_SERVO_DEGREES)
        self._send(struct.pack("f", degrees))

        return self._recv_result()
    
    def get_motor_voltage_lut(self, steps: int, should_save_lut_to_persistent_storage: bool) -> str:
        self._send_opcode(Opcodes.GET_MOTOR_VOLTAGE_LUT)
        self._send(struct.pack("I?", steps, should_save_lut_to_persistent_storage))
        return self._recv_string()
    
    def get_servo_degrees_lut(self, steps: int, should_save_lut_to_persistent_storage: bool) -> str:
        self._send_opcode(Opcodes.GET_SERVO_DEGREES_LUT)
        self._send(struct.pack("B?", steps, should_save_lut_to_persistent_storage))
        return self._recv_string()
    
    def set_acceleration(self, acceleration: float):
        self._send_opcode(Opcodes.SET_ACCELERATION)
        self._send(struct.pack("f", acceleration))

        return self._recv_result()
    
    def set_hid_controller(self, throttle_and_brake: int, steering: int):
        self._send_opcode(Opcodes.SET_HID_CONTROLLER)
        self._send(struct.pack("hh", throttle_and_brake, steering))

        return self._recv_result()
    
    def emergency_stop(self):
        self._send_opcode(Opcodes.EMERGENCY_STOP)
        self.keep_alive_thread.terminate()
        self.arduino.close()

    def _keep_alive(self):
        while True:
            self._send(0x02)
            self._recv(1)
            time.sleep(1)

    def _send(self, data: bytes):
        self.comms_lock.acquire()
        self.arduino.write(data)
        self.comms_lock.release()

    def _send_opcode(self, opcode: Opcodes):
        self._send(struct.pack("B", opcode.value))

    def _recv(self, len: int) -> bytes:
        self.comms_lock.acquire()
        res = self.arduino.read(len)
        self.comms_lock.release()

        return res
    
    def _recv_result(self) -> Results:
        return Results(struct.unpack("B", self._recv(1))[0])

    def _recv_string(self) -> str:
        self.comms_lock.acquire()
        res = self.arduino.read_until(b"\x00")
        self.comms_lock.release()
        
        return str(res, "utf-8")