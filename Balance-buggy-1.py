from machine import Pin, PWM
from time import sleep

# Motor A
A1 = PWM(Pin(0))
A2 = PWM(Pin(1))

# Motor B
B1 = PWM(Pin(14))
B2 = PWM(Pin(15))

# Configure PWM frequency
A1.freq(1000)   # 1 kHz - not silent
A2.freq(1000)   # Set frequency for A2
B1.freq(1000)
B2.freq(1000)   # Set frequency for B2

MAX_SPEED = 30000  # Max duty cycle for 16-bit PWM

def motor_a(speed):
    """Speed from -1.0 to +1.0"""
    assert -1.0 <= speed <= 1.0, "Speed must be between -1.0 and +1.0"
    print("Motor A speed:", speed)
    if speed == 0:
        A1.duty_u16(0)
        A2.duty_u16(0)
    elif speed > 0:
        A1.duty_u16(int(MAX_SPEED * speed))
        A2.duty_u16(0)
    else:
        A1.duty_u16(0)
        A2.duty_u16(int(MAX_SPEED * -speed))  # reverse full

def motor_b(speed):
    """Speed from -1.0 to +1.0"""
    assert -1.0 <= speed <= 1.0, "Speed must be between -1.0 and +1.0"
    print("Motor B speed:", speed)
    if speed == 0:
        B1.duty_u16(0)
        B2.duty_u16(0)
    elif speed > 0:
        B1.duty_u16(int(MAX_SPEED * speed))
        B2.duty_u16(0)
    else:
        B1.duty_u16(0)
        B2.duty_u16(int(MAX_SPEED * -speed))

# test
try:
    while True:
        motor_a(0.5)
        motor_b(0.5)
        sleep(1)
        motor_a(-0.5)
        motor_b(-0.5)
        sleep(1)
except KeyboardInterrupt:
    motor_a(0)
    motor_b(0)
    print("Done, motors off.")
# Issues:
# 1. Only A1 and B1 have their frequency set; A2 and B2 should also have .freq(1000) set.
# 2. MAX_SPEED is 30000, but PWM.duty_u16() expects a value from 0 to 65535. This limits the maximum speed.
# 3. No explicit stop for A2/B2 on positive speed, or A1/B1 on negative speed, but the logic is correct for H-bridge.
# 4. No hardware safety checks (e.g., for out-of-range speed values).
# 5. The code will not be "silent" at 1kHz; for quieter operation, use a higher frequency (e.g., 20kHz).
# 6. No cleanup for PWM objects on exit (not critical for Pico, but good practice).
