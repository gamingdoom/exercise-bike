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

class ExerciseBike:
    def __init__(self, mode_flags: ModeFlags, serial_port: str = "/dev/ttyACM0", baud_rate: int = 115200):
        self.mode_flags = mode_flags

        self.arduino = serial.Serial(serial_port, baud_rate)
    
    def start(self):
        # Send start message
        self._send(0x01)
        self._send(self.mode_flags)

        # Receive start message
        if self._recv(1) != Results.SUCCESS:
            raise Exception("Failed to connect to bike!")
        
        # Launch thread that keeps connection alive
        self.comms_lock = Lock()
        self.keep_alive_thread = Process(target=self._keep_alive)
        self.keep_alive_thread.start()
        
    def close(self):
        self.keep_alive_thread.terminate()
        self._send(0x03)
        res = self._recv(1)

        return res
        
    def get_wheel_velocity(self) -> float:
        self._send(0x04)
        return struct.unpack("f", self._recv(4))[0]
    
    def set_motor_voltage(self, voltage: float):
        self._send(0x05)
        self._send(struct.pack("f", voltage))

        return self._recv(1)
        
    def set_servo_degrees(self, degrees: float):
        self._send(0x06)
        self._send(struct.pack("f", degrees))

        return self._recv(1)
    
    def get_motor_voltage_lut(self, steps: int, should_save_lut_to_persistent_storage: bool) -> str:
        self._send(0x07)
        self._send(struct.pack("I?", steps, should_save_lut_to_persistent_storage))
        return self._recv_string()
    
    def get_servo_degrees_lut(self, steps: int, should_save_lut_to_persistent_storage: bool) -> str:
        self._send(0x08)
        self._send(struct.pack("B?", steps, should_save_lut_to_persistent_storage))
        return self._recv_string()
    
    def set_acceleration(self, acceleration: float):
        self._send(0x09)
        self._send(struct.pack("f", acceleration))

        return self._recv(1)
    
    def set_hid_throttle_and_brake(self, throttle_and_brake: int):
        self._send(0x0A)
        self._send(struct.pack("h", throttle_and_brake))

        return self._recv(1)
    
    def emergency_stop(self):
        self._send(0x0B)
        self.keep_alive_thread.terminate()

    def _keep_alive(self):
        while True:
            self._send(0x02)
            self._recv(1)
            time.sleep(1)

    def _send(self, data: bytes):
        self.comms_lock.acquire()
        self.arduino.write(data)
        self.comms_lock.release()
        
    def _recv(self, len: int) -> bytes:
        self.comms_lock.acquire()
        res = self.arduino.read(len)
        self.comms_lock.release()

        return res

    def _recv_string(self) -> str:
        self.comms_lock.acquire()
        res = self.arduino.read_until(b"\x00")
        self.comms_lock.release()
        
        return str(res, "utf-8")