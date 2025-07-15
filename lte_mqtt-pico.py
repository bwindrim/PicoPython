"""
MicroPython async MQTT test over 4G
"""

import lte
import time
from mqtt_async import MQTTClient, config
import uasyncio as asyncio
from machine import Pin, PWM, UART

MOBILE_APN = "iot.1nce.net"

# Fix the eye-searing brightness of the onboard LED with PWM
class Netlight:
    def __init__(self):
        self.pin = PWM(Pin("LED", Pin.OUT), freq=1000)

    def value(self, value):
        self.pin.duty_u16(value * 2000)


con = lte.LTE(MOBILE_APN, uart=UART(0, tx=Pin(16, Pin.OUT), rx=Pin(17, Pin.IN)), reset_pin=Pin(18, Pin.OUT), netlight_pin=Pin(19, Pin.IN), netlight_led=Netlight())
con.start_ppp(baudrate=115200) # stay at the Clipper module's default baudrate


# Change the following configs to suit your environment
TOPIC           = 'BWtest/mqtt_async'
config.server   = 'broker.hivemq.com' # can also be a hostname
#config.ssid     = 'wifi-ssid'
#config.wifi_pw  = 'wifi-password'

def callback(topic, msg, retained, qos): print(topic, msg, retained, qos)

async def conn_callback(client): await client.subscribe(TOPIC, 1)

async def main(client):
    await client.connect()
    print("MQTT connected!")
    n = 0
    while True:
        print('publish', n)
        await client.publish(TOPIC, 'Hello World #{}!'.format(n), qos=1)
        await asyncio.sleep(5)
        n += 1

config.subs_cb = callback
config.connect_coro = conn_callback

try:
    t_start = time.time()
    client = MQTTClient(config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(client))

finally:
    t_end = time.time()
    print(f"Took: {t_end - t_start} seconds")
    print("Disconnecting...")
    con.stop_ppp()
    print("Done!")