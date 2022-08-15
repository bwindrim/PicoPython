import network
import time
import machine

led = machine.Pin("LED", machine.Pin.OUT)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('Ardfern Motorhome Park', 'ARDFERNMP')

while not wlan.isconnected() and wlan.status() >= 0:
    print("Waiting to connect:")
    led.toggle()
    time.sleep(1)

led.on()
print(wlan.ifconfig())
