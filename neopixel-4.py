import time
import network
import socket
import machine
import rp2
import ubinascii
from neopixel import NeoPixel
from math import sin, radians, fabs, pow


ssids = {
    'BedroomTestNetwork': 'dvdrtsPnk4xq'
    }

# Configure the number of WS2812 LEDs, pins and brightness.
NUM_NEOPIXELS = 60 # ItsyBitsy RP2040 only has one neopixel
PWR_PIN = 26      # GPIO26 is the 74AHCT125N output 4 enable (active low)
NEOPIXEL_PIN = 22 # GPIO22 on NeoPixel controller Pico Zero board
LED_PIN = "LED"   # let MicroPython decide which pin controls the on-board LED

g_brightness = 0.5 # global brightness setting, range 0.0 - 1.0
g_gamma = 2.2

def pixel_value(color):
        r = int(color[0] * g_brightness)
        g = int(color[1] * g_brightness)
        b = int(color[2] * g_brightness)
        return (r, g, b)
    
def pixels_fill(rgb):
    # treat time in seconds as degrees of angle
    r = (int(255 * rgb[0] * g_brightness) for i in range(len(np)))
    g = (int(255 * rgb[1] * g_brightness) for i in range(len(np)))
    b = (int(255 * rgb[2] * g_brightness) for i in range(len(np)))
    for i, c in enumerate(zip(r, g, b)):
        np[i] = c
   
def gamma(encoded):
    return pow(encoded, 2.2)

def pixels_fill2(time):
    # treat time in seconds as degrees of angle
    r = (int(0.5 + 255.0 * gamma(fabs(sin(radians((time + i)*3.0))) * g_brightness)) for i in range(len(np)))
    g = (int(0.5 + 255.0 * gamma(fabs(sin(radians((time + i)*6.0))) * g_brightness)) for i in range(len(np)))
    b = (int(0.5 + 255.0 * gamma(fabs(sin(radians((time + i)*9.0))) * g_brightness)) for i in range(len(np)))
    for i, c in enumerate(zip(r, g, b)):
        np[i] = c
   
def gamma2(encoded):
    return int(0.5 + 255.0 * pow(encoded*g_brightness, g_gamma))

def gamma3(encoded):
    return (int(0.5 + 255.0 * pow(encoded[0]*g_brightness, g_gamma)),
            int(0.5 + 255.0 * pow(encoded[1]*g_brightness, g_gamma)),
            int(0.5 + 255.0 * pow(encoded[2]*g_brightness, g_gamma)))

def shader1(time, x, y=0):
    # treat time in seconds as degrees of angle
    angle = radians(time + x)
    return (fabs(sin(angle*3.0)), fabs(sin(angle*6.0)), fabs(sin(angle*9.0)))

def shader2(time, x, y=0):
    # treat time in seconds as degrees of angle
    assert(y == 0)
    angle = radians(time + x)*6.0 # map 60 seconds to full circle
    return ((1.0 + sin(angle*1.0))/2, (1.0 + sin(angle*2.0))/2, (1.0 + sin(angle*3.0))/2)

# def shader3(time, x, y=0):
#     # treat time in seconds as degrees of angle
#     angle = radians(time + x)*6.0
#     return ((1.0 + sin(angle))/2, (1.0 + sin(angle + angle))/2, (1.0 + sin(angle + angle + angle))/2)

def grayscale1(time, x, y=0): # grey ramp
    return ((x / 59.0), (x / 59.0), (x / 59.0))

def pixels_fill3(shader, time, width, height=1):
    for i, c in enumerate(shader(time, x, y) for x in range(width) for y in range(height)):
#        np[i] = tuple(map(gamma2, c))
        np[i] = gamma3(c)
        
pwr = machine.Pin(PWR_PIN, machine.Pin.OUT)
led = machine.Pin(LED_PIN, machine.Pin.OUT)
pin = machine.Pin(NEOPIXEL_PIN, machine.Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, NUM_NEOPIXELS)   # create NeoPixel driver

BLACK   = (0.0, 0.0, 0.0)
WHITE   = (1.0, 1.0, 1.0)
RED     = (1.0, 0.0, 0.0)
GREEN   = (0.0, 1.0, 0.0)
BLUE    = (0.0, 0.0, 1.0)
YELLOW  = (1.0, 1.0, 0.0)
CYAN    = (0.0, 1.0, 1.0)
MAGENTA = (1.0, 0.0, 1.0)

rgb = WHITE
color = "FFFFFF"

pwr.value(0) # enable the NeoPixel output
start = time.ticks_ms() # get millisecond counter
loop_prev = start
render_max = 0
while True:
    loop_start = time.ticks_ms()
    delta = time.ticks_diff(loop_start, start) /1000.0 # compute time difference
    #print("delta_secs =", delta_secs)
    loop_prev = loop_start
    pixels_fill3(shader2, delta, len(np))
    np.write()
    render_time = time.ticks_diff(time.ticks_ms(), loop_start)
    if render_time > render_max:
        render_max = render_time
        print("render time =", render_time, "ms")
    assert(render_time < 60.0)
    time.sleep_ms(100 - render_time)

