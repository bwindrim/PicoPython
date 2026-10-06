# DC_motor_test-1.py
#
# Raspberry Pi Pico - DC motor motion demo
#
# Demonstrates operating DC motors driven by a L9110.
#

# load standard Python modules
import math, time
from machine import Pin, PWM

# print a banner as reminder of what code is loaded
print("Starting buggy motor test")

#--------------------------------------------------------------------------------
# Class to represent a single L9110 H-bridge driver.

class L9110():
    def __init__(self, IA=18, IB=19, pwm_rate=20000):
        # Create a pair of PWMOut objects for each motor channel.
        self.ia = PWM(Pin(IA))
        self.ia.freq(pwm_rate)
        self.ia.duty_u16(0)
        self.ib = PWM(Pin(IB))
        self.ib.freq(pwm_rate)
        self.ib.duty_u16(0)

    def write(self, rate):
        """Set the speed and direction on a single motor channel.

        :param rate: modulation value between -1.0 and 1.0, full reverse to full forward."""

        # convert the rate into a 16-bit fixed point integer
        pwm = min(max(int(2**16 * abs(rate)), 0), 65535)
        print("pwm =", pwm)
        if rate < 0:
            self.ia.duty_u16(0)
            self.ib.duty_u16(pwm)
        else:
            self.ib.duty_u16(0)
            self.ia.duty_u16(pwm)


#--------------------------------------------------------------------------------
# Create an object to represent a motor driver.
print("Creating driver objects")
motor1 = L9110(IA=12, IB=13)
motor2 = L9110(IA=14, IB=15)
motor3 = L9110(IA=16, IB=17)
motor4 = L9110(IA=18, IB=19)

motors = [motor1, motor2, motor3, motor4]

def write_motors(motors, duty=0.0):
    for motor in motors:
        motor.write(duty)

def test_motor(driver):
    driver.write(1.0) # full forward
    time.sleep(2.0)

    driver.write(0.0)
    time.sleep(0.5)

    driver.write(-1.0) # full reverse
    time.sleep(2.0)
    
    driver.write(0.0) # stop
    time.sleep(0.5)

def ramp_test(driver):
    for i in range(7, 10):
        print("Duty =", i)
        driver.write(i*0.1)
        time.sleep(1.0)

    driver.write(0.0)
    time.sleep(0.5)
        
    for i in range(7, 10):
        print("Duty = -", i)
        driver.write(-i*0.1)
        time.sleep(1.0)
        
    driver.write(0.0)
    time.sleep(0.5)
        
#--------------------------------------------------------------------------------
# Begin the main processing loop.  This is structured as a looping script, since
# each movement primitive 'blocks', i.e. doesn't return until the action is
# finished.

print("Starting main script.")
try:
    write_motors(motors, 1.0)
    time.sleep(1.0)
    write_motors(motors, 0.0)
    time.sleep(1.0)
    write_motors(motors, -1.0)
    time.sleep(1.0)
    write_motors(motors, 0.0)
    time.sleep(1.0)

    for motor in motors:
        print("Testing.")
        test_motor(motor)
    
    for motor in motors:
        print("Ramp test.")
        ramp_test(motor)
        
except KeyboardInterrupt:
    pass

for motor in motors:
    motor.write(0)

