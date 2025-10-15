# MicroPython PWM DC motor control for Raspberry Pi Pico using H-bridge on GPIO 12 and 13

import machine
import time

# H-bridge inputs
pin1 = machine.PWM(machine.Pin(14))
pin2 = machine.PWM(machine.Pin(15))

# Set PWM frequency (Hz)
FREQ = 1000
pin1.freq(FREQ)
pin2.freq(FREQ)

def move_motor(forward=True, duty=65535):
    if forward:
        pin2.duty_u16(0)
        pin1.duty_u16(duty)
    else:
        pin1.duty_u16(0)
        pin2.duty_u16(duty)

def ramp(duty_start, duty_end, step, forward=True, delay=0.01):
    if duty_start < duty_end:
        rng = range(duty_start, duty_end, step)
    else:
        rng = range(duty_start, duty_end, -step)
    for d in rng:
        move_motor(forward, d)
        time.sleep(delay)
    move_motor(forward, duty_end)

max_duty = 20000  # Max duty cycle for 16-bit PWM
try:
    while True:
        # Ramp up forward
        ramp(0, max_duty, 1000, forward=True)
        time.sleep(2)
        # Ramp down forward
        ramp(max_duty, 0, 1000, forward=True)
        # Ramp up reverse
        ramp(0, max_duty, 1000, forward=False)
        time.sleep(2)
        # Ramp down reverse
        ramp(max_duty, 0, 1000, forward=False)
except KeyboardInterrupt:
    pin1.duty_u16(0)
    pin2.duty_u16(0)
    print("Done, motor off.")
