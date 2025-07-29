"""
MicroPython async MQTT test over 4G
"""

import lte
import time
from mqtt_async import MQTTClient, config
import asyncio
import uaqueue
from machine import Pin, UART

from machine import UART
import uasyncio as asyncio

import sys_constants

hex_encode = True

uart = UART(1, baudrate=57600)

class Netlight:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.OUT)
        self.override = True  # True to override the pin state
        self.state = 0  # 0 for low, 1 for high
        self.pin.value(0)  # Start with the pin low

    def value(self, value):
        """Set the pin value, overriding if necessary."""
        if self.override:
            self.pin.value(self.state)
        else:
            # If not overriding, set the pin to the given value
            self.pin.value(value)

# -------- COBS Encoding / Decoding --------
"""
Consistent Overhead Byte Stuffing (COBS)

This version is for Python 3.x.
"""


class DecodeError(Exception):
    pass


def _get_buffer_view(in_bytes):
    mv = memoryview(in_bytes)
#    if mv.ndim > 1 or mv.itemsize > 1:
#        raise BufferError('object must be a single-dimension buffer of bytes.')
    try:
        if mv.format != 'B':
            mv = mv.cast('B')
    except AttributeError:
        pass
    return mv

def cobs_encode(in_bytes: bytes) -> bytes:
    """Encode a string using Consistent Overhead Byte Stuffing (COBS).
    
    Input is any byte string. Output is also a byte string.
    
    Encoding guarantees no zero bytes in the output. The output
    string will be expanded slightly, by a predictable amount.
    
    An empty string is encoded to '\\x01'"""
    if isinstance(in_bytes, str):
        raise TypeError('Unicode-objects must be encoded as bytes first')
    in_bytes_mv = _get_buffer_view(in_bytes)
    final_zero = True
    out_bytes = bytearray()
    idx = 0
    search_start_idx = 0
    for in_char in in_bytes_mv:
        if in_char == 0:
            final_zero = True
            out_bytes.append(idx - search_start_idx + 1)
            out_bytes += in_bytes_mv[search_start_idx:idx]
            search_start_idx = idx + 1
        else:
            if idx - search_start_idx == 0xFD:
                final_zero = False
                out_bytes.append(0xFF)
                out_bytes += in_bytes_mv[search_start_idx:idx+1]
                search_start_idx = idx + 1
        idx += 1
    if idx != search_start_idx or final_zero:
        out_bytes.append(idx - search_start_idx + 1)
        out_bytes += in_bytes_mv[search_start_idx:idx]
    return bytes(out_bytes)


def cobs_decode(in_bytes: bytes) -> bytes:
    """Decode a string using Consistent Overhead Byte Stuffing (COBS).
    
    Input should be a byte string that has been COBS encoded. Output
    is also a byte string.
    
    A cobs.DecodeError exception will be raised if the encoded data
    is invalid."""
    if isinstance(in_bytes, str):
        raise TypeError('Unicode-objects are not supported; byte buffer objects only')
    in_bytes_mv = _get_buffer_view(in_bytes)
    out_bytes = bytearray()
    idx = 0

    if len(in_bytes_mv) > 0:
        while True:
            length = in_bytes_mv[idx]
            if length == 0:
                raise DecodeError("zero byte found in input")
            idx += 1
            end = idx + length - 1
            copy_mv = in_bytes_mv[idx:end]
            # MicroPython doesn't support 'in' for memoryview, so use a loop
            for b in copy_mv:
                if b == 0:
                    raise DecodeError("zero byte found in input")
            out_bytes += copy_mv
            idx = end
            if idx > len(in_bytes_mv):
                raise DecodeError("not enough input bytes for length code")
            if idx < len(in_bytes_mv):
                if length < 0xFF:
                    out_bytes.append(0)
            else:
                break
    return bytes(out_bytes)

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

mqtt_rx_queue = uaqueue.Queue()
uart_rx_queue = uaqueue.Queue()

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
    # Append the message to the MQTT RX queue
    # Message callbacks are non-async, so we use put_nowait to avoid blocking.
    mqtt_rx_queue.put_nowait((topic, msg, retained, qos))

async def conn_callback(client):
    """Callback function to handle MQTT connection events.
    This function will be called when the client connects to the MQTT broker.
    """
    netlight.override = False  # Allow the netlight to be controlled by the MQTT client
    print("MQTT connected, subscribing to", sys_constants.SUBSCRIBE_TOPIC)
    # Subscribe to the topic with QoS level 1
    await client.subscribe(sys_constants.SUBSCRIBE_TOPIC, 1)

async def mqtt_rx_queue_reader():
    while True:
        topic, msg, retained, qos = await mqtt_rx_queue.get()
        print("Received from MQTT RX queue:", topic, msg.hex(), retained, qos)
        frame = cobs_encode(msg)  # encode the message as COBS
        frame += b'\x00'          # append a zero byte to frame
        # Send the encoded message over UART in chunks of 8 bytes, so as
        # not to over-fill the UART Tx FIFO and hence block async execution.
        print("Sending to UART:", frame.hex())
        for i in range(0, len(frame), 8):
            uart.write(frame[i:i+8])
            await asyncio.sleep(0)  # cooperative yield

async def uart_rx_queue_reader():
    while True:
        msg = await uart_rx_queue.get()
        print("Received from UART RX queue:", msg)
        if hex_encode:
            # Encode the message to hex if hex_encode is True
            msg = msg.hex().encode('utf-8')
        await client.publish(sys_constants.PUBLISH_TOPIC, msg, qos=1)

async def main():
    asyncio.create_task(uart_rx_loop())
    asyncio.create_task(mqtt_rx_queue_reader())
    asyncio.create_task(uart_rx_queue_reader())
    await client.connect()
    print("MQTT connected!")
    while True:
        await asyncio.sleep(1)
#        print("Waiting for messages...")

# MQTT configuration
# Note: broker.hivemq.com is a public broker, so no authentication is required.
# If you want to use a private broker, you can set the username and password in the config.
# For example:
# config.username = 'your-username'
# config.password = 'your-password'
# The topic can be changed to whatever you want to publish/subscribe to.
# The QoS level can also be adjusted as needed (0, 1, or 2).
# The default QoS is 1, which means the message will be delivered at least once
config.server   = sys_constants.BROKER_ADDR # can be an IP address or a hostname
config.subs_cb = callback
config.connect_coro = conn_callback

netlight = Netlight("LED")  # Use the built-in LED pin for netlight indication
netlight.state = 1  # Turn on the netlight to indicate the script is running

# Initialize the LTE connection
con = lte.LTE(sys_constants.MOBILE_APN, uart=UART(0, tx=Pin(16, Pin.OUT), rx=Pin(17, Pin.IN)), reset_pin=Pin(18, Pin.OUT), netlight_pin=Pin(19, Pin.IN), netlight_led=netlight)
con.start_ppp(baudrate=115200) # stay at the Clipper module's default baudrate

try:
    t_start = time.time()
    client = MQTTClient(config)
    asyncio.run(main())
except KeyboardInterrupt:
    print("KeyboardInterrupt: stopping...")
finally:
    t_end = time.time()
    print(f"Took: {t_end - t_start} seconds")
    print("Disconnecting...")
    client.disconnect()
    con.stop_ppp()
    netlight.override = True  # Allow the netlight to be controlled
    netlight.state = 0  # Turn off the netlight
    netlight.value(0)
    print("Done!")