import lte
import time
import requests
from machine import Pin, PWM, UART


MOBILE_APN = "iot.1nce.net"

# Setting this to True will attempt to resume an existing connection
RESUME = False

# Fix the eye-searing brightness of the onboard LED with PWM
class Netlight:
    def __init__(self):
        self.pin = PWM(Pin("LED", Pin.OUT), freq=1000)

    def value(self, value):
        self.pin.duty_u16(value * 2000)


con = lte.LTE(MOBILE_APN, uart=UART(0), reset_pin=Pin(7, Pin.OUT), netlight_pin=Pin(6, Pin.IN), netlight_led=Netlight(), skip_reset=RESUME)
con.start_ppp(connect=not RESUME)

# Do some requests! Internet stuff should just work now.
try:
    t_start = time.time()
    for x in range(2):
        req = requests.get("https://shop.pimoroni.com/robots.txt")
        print(req)

finally:
    t_end = time.time()

    print(f"Took: {t_end - t_start} seconds")

    print("Disconnecting...")
    con.stop_ppp()
    print("Done!")