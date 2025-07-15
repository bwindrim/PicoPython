"""
MicroPython async MQTT test over 4G
"""

import lte
import time
from mqtt_async import MQTTClient, config
import asyncio
from machine import Pin, PWM, UART

MOBILE_APN = "iot.1nce.net"

def callback(topic, msg, retained, qos):
    """Callback function to handle incoming messages.
    This function will be called whenever a message is received on the subscribed topic.
    """
    # Print the topic, message, retained flag, and QoS level
    print(topic, msg, retained, qos)

async def conn_callback(client):
    print("MQTT connected, subscribing to", SUBSCRIBE_TOPIC)
    # Subscribe to the topic with QoS level 1
    await client.subscribe(SUBSCRIBE_TOPIC, 1)

async def main(client):
    await client.connect()
    print("MQTT connected!")
    n = 0
    while True:
        print('publish', n)
        await client.publish(PUBLISH_TOPIC, f'Hello World #{n}!', qos=1)
        await asyncio.sleep(5)
        n += 1

# MQTT configuration
# Note: broker.hivemq.com is a public broker, so no authentication is required.
# If you want to use a private broker, you can set the username and password in the config.
# For example:
# config.username = 'your-username'
# config.password = 'your-password'
# The topic can be changed to whatever you want to publish/subscribe to.
# The QoS level can also be adjusted as needed (0, 1, or 2).
# The default QoS is 1, which means the message will be delivered at least once
SUBSCRIBE_TOPIC = 'BWtest/mqtt_async'
PUBLISH_TOPIC   = 'BWtest/mqtt_async'
config.server   = 'broker.hivemq.com' # can be an IP address or a hostname
config.subs_cb = callback
config.connect_coro = conn_callback

# Initialize the LTE connection
con = lte.LTE(MOBILE_APN, uart=UART(0, tx=Pin(16, Pin.OUT), rx=Pin(17, Pin.IN)), reset_pin=Pin(18, Pin.OUT), netlight_pin=Pin(19, Pin.IN), netlight_led=Pin("LED", Pin.OUT))
con.start_ppp(baudrate=115200) # stay at the Clipper module's default baudrate

try:
    t_start = time.time()
    client = MQTTClient(config)
    asyncio.run(main(client))
except KeyboardInterrupt:
    print("KeyboardInterrupt: stopping...")
finally:
    t_end = time.time()
    print(f"Took: {t_end - t_start} seconds")
    print("Disconnecting...")
    con.stop_ppp()
    print("Done!")