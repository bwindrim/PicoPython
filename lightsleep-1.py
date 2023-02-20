import machine
import time

count = 0
hour_in_ms = 60 * 60 * 1000
led = machine.Pin(25, machine.Pin.OUT, value=1)

while True:
    print ("count =", count)
    count += 1
    time.sleep_ms(500)
    led.off()
    machine.lightsleep(1)
    led.on()
