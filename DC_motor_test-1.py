# dual_spin.py
#
# Raspberry Pi Pico - DC motor motion demo
#
# Demonstrates operating two DC motors driven by a DRV8833.
#
# This assumes a Pololu DRV8833 dual motor driver has been wired up to the Pico as follows:
#   Pico pin 24, GPIO18   -> AIN1
#   Pico pin 25, GPIO19   -> AIN2
#   Pico pin 26, GPIO20   -> BIN2
#   Pico pin 27, GPIO21   -> BIN1
#   any Pico GND          -> GND

# DRV8833 carrier board: https://www.pololu.com/product/2130

################################################################
# CircuitPython module documentation:
# time    https://circuitpython.readthedocs.io/en/latest/shared-bindings/time/index.html
# math    https://circuitpython.readthedocs.io/en/latest/shared-bindings/math/index.html
# board   https://circuitpython.readthedocs.io/en/latest/shared-bindings/board/index.html
# pwmio   https://circuitpython.readthedocs.io/en/latest/shared-bindings/pwmio/index.html

################################################################################
# print a banner as reminder of what code is loaded
print("Starting dual_spin script.")

# load standard Python modules
import math, time
from machine import Pin, PWM

#--------------------------------------------------------------------------------
# Class to represent a single dual H-bridge driver.

class L9110():
    def __init__(self, IA=14, IB=15, pwm_rate=20000):
        # Create a pair of PWMOut objects for each motor channel.
        self.ia = PWM(Pin(IA))
        self.ia.freq(pwm_rate)
        self.ia.duty_u16(0)
        self.ib = PWM(Pin(IB))
        self.ib.freq(pwm_rate)
        self.ib.duty_u16(0)

    def write(self, rate):
        """Set the speed and direction on a single motor channel.

        :param channel:  0 for motor A, 1 for motor B
        :param rate: modulation value between -1.0 and 1.0, full reverse to full forward."""

        # convert the rate into a 16-bit fixed point integer
        pwm = min(max(int(2**16 * abs(rate)), 0), 65535)

        if rate < 0:
            self.ia.duty_u16(0)
            self.ib.duty_u16(pwm)
        else:
            self.ib.duty_u16(0)
            self.ia.duty_u16(pwm)


#--------------------------------------------------------------------------------
# Create an object to represent a dual motor driver.
print("Creating driver object.")
driver = L9110()

#--------------------------------------------------------------------------------
# Begin the main processing loop.  This is structured as a looping script, since
# each movement primitive 'blocks', i.e. doesn't return until the action is
# finished.

print("Starting main script.")
try:
    # initial pause
    time.sleep(2.0)

    print("Testing.")
    driver.write(1.0)
    time.sleep(2.0)

    driver.write(0.0)
    time.sleep(2.0)

    driver.write(-1.0)
    time.sleep(2.0)
    
    driver.write(0.0)
    time.sleep(2.0)
    print("Ramp test.")

    for i in range(10):
        print("Duty =", i)
        driver.write(i*0.1)
        driver.write(i*0.1)
        time.sleep(0.5)

    driver.write(0.0)
    driver.write(0.0)
    time.sleep(2.0)
        
    for i in range(10):
        print("Duty = -", i)
        driver.write(-i*0.1)
        driver.write(-i*0.1)
        time.sleep(0.5)
        
except KeyboardInterrupt:
    pass

driver.write(0.0)
driver.write(0.0)
print("Finished.")
