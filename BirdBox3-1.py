from machine import Pin, Timer
import time

def wait_pin_change(pin):
    "Debounce a GPIO input"
    # wait for pin to change value
    # it needs to be stable for a continuous 20ms
    cur_value = pin.value()
    active = 0
    while active < 20:
        if pin.value() != cur_value:
            active += 1
        else:
            active = 0
        time.sleep_ms(1)
    return cur_value
        
led = Pin(25, Pin.OUT)
pwr = Pin(22, Pin.OUT, value=1)
btn = Pin(12, Pin.IN, Pin.PULL_UP)
timer = Timer()

def blink(timer):
    led.toggle()

#timer.init(freq=2.5, mode=Timer.PERIODIC, callback=blink)

enable = True
while True:
    led.value(enable)
    pwr.value(enable)
    if 0 == wait_pin_change(btn):
        enable = not enable
    