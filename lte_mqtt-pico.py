"""
MicroPython async MQTT test over 4G
"""

import lte
import time
from mqtt_async import MQTTClient, config
import asyncio
import queue
from machine import Pin, UART
#import uartcobs

from machine import UART
import uasyncio as asyncio

hex_encode = True

uart = UART(1, baudrate=57600)

# -------- COBS Encoding / Decoding --------

def cobs_encode(data: bytes) -> bytes:
    output = bytearray()
    idx = 0
    while idx < len(data):
        block_start = idx
        code = 1
        output.append(0)  # placeholder
        while idx < len(data) and data[idx] != 0 and code < 0xFF:
            output.append(data[idx])
            idx += 1
            code += 1
        output[block_start] = code
        if idx < len(data) and data[idx] == 0:
            idx += 1  # skip zero byte
    output.append(0)  # frame delimiter
    return bytes(output)

def cobs_decode(frame: bytes) -> bytes:
    output = bytearray()
    idx = 0
    while idx < len(frame):
        code = frame[idx]
        if code == 0 or idx + code > len(frame):
            raise ValueError("Invalid COBS frame")
        idx += 1
        output.extend(frame[idx:idx + code - 1])
        idx += code - 1
        if code < 0xFF and idx < len(frame):
            output.append(0)
    return bytes(output)

# -------- Async UART Loops --------

async def uart_rx_loop():
    """COBS-based receiver using async polling."""
    rxbuf = bytearray()
    while True:
        if uart.any():
            data = uart.read(1)
            if data:
                b = data[0]
                if b == 0:
                    if rxbuf:
                        try:
                            msg = cobs_decode(rxbuf)
                            #print("Received from UART:", msg)
                            # append the message to the UART RX queue
                            await uart_rx_queue.put(msg)
                        except ValueError:
                            print("Bad frame")
                        rxbuf = bytearray()
                else:
                    rxbuf.append(b)
        await asyncio.sleep_ms(2)

async def uart_send(msg: bytes):
    """COBS-encodes and writes a message to UART."""
    frame = cobs_encode(msg)
    uart.write(frame)
    await asyncio.sleep_ms(0)  # Yield to event loop

MOBILE_APN = "iot.1nce.net"

mqtt_rx_queue = queue.Queue()
uart_rx_queue = queue.Queue()

def callback(topic, msg, retained, qos):
    """Callback function to handle incoming messages.
    This function will be called whenever a message is received on the subscribed topic.
    """
    # Print the topic, message, retained flag, and QoS level
    print(topic, msg, retained, qos)
    if hex_encode:
        # Decode the message from hex if hex_encode is True
        try:
            msg = bytes.fromhex(msg.decode('utf-8'))
        except ValueError:
            print("Error decoding hex message")
            return
    await mqtt_rx_queue.put((topic, msg, retained, qos))

async def conn_callback(client):
    print("MQTT connected, subscribing to", SUBSCRIBE_TOPIC)
    # Subscribe to the topic with QoS level 1
    await client.subscribe(SUBSCRIBE_TOPIC, 1)

async def mqtt_rx_queue_reader():
    while True:
        topic, msg, retained, qos = await mqtt_rx_queue.get()
        print("Received from MQTT RX queue:", topic, msg, retained, qos)
        await uart_send(msg)  # forward the message to the UART

async def uart_rx_queue_reader():
    while True:
        msg = await uart_rx_queue.get()
        print("Received from UART RX queue:", msg)
        if hex_encode:
            # Encode the message to hex if hex_encode is True
            msg = msg.hex().encode('utf-8')
        await client.publish(PUBLISH_TOPIC, msg, qos=1)

async def main(client):
    asyncio.create_task(uart_rx_loop())
    asyncio.create_task(mqtt_rx_queue_reader())
    asyncio.create_task(uart_rx_queue_reader())
    await client.connect()
    print("MQTT connected!")
    await asyncio.sleep(0) # Yield control to allow conn_callback to complete its subscribe
    n = 0
    while True:
        print('publish', n)
        msg = f'Hello World #{n}!'.encode('utf-8')
        await client.publish(SUBSCRIBE_TOPIC, msg.hex().encode('utf-8'), qos=1)
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
SUBSCRIBE_TOPIC = 'BWtest/mqtt_async/0/in'
PUBLISH_TOPIC   = 'BWtest/mqtt_async/0/out'
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