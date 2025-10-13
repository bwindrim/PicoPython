from machine import Pin, Timer
led = Pin("LED", Pin.OUT) # 25 for Pico (non-W), 11 for ItsyBitsy
timer = Timer()

def blink(timer):
    led.toggle()

timer.init(freq=2.5, mode=Timer.PERIODIC, callback=blink)

while True:
    pass