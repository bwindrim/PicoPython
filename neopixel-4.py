import time
import network
import socket
import machine
import rp2
import ubinascii
from neopixel import NeoPixel
from math import sin, radians, fabs, pow, ceil

BLACK   = (0.0, 0.0, 0.0)
WHITE   = (1.0, 1.0, 1.0)
RED     = (1.0, 0.0, 0.0)
GREEN   = (0.0, 1.0, 0.0)
BLUE    = (0.0, 0.0, 1.0)
YELLOW  = (1.0, 1.0, 0.0)
CYAN    = (0.0, 1.0, 1.0)
MAGENTA = (1.0, 0.0, 1.0)

# Configure the number of WS2812 LEDs, pins and brightness.
NUM_NEOPIXELS = 60 
PWR_PIN = 26      # GPIO26 is the 74AHCT125N output 4 enable (active low)
NEOPIXEL_PIN = 22 # GPIO22 on NeoPixel controller Pico Zero board
LED_PIN = "LED"   # let MicroPython decide which pin controls the on-board LED

g_gamma = 2.0
g_brightness = 255.0*pow(1.0, g_gamma) # global brightness setting, range 0.0 - 1.0

def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))

def saturate(value):
#     assert(value >= 0.0)
#     assert(value <= 1.0)
    return clamp(value, 0.0, 1.0)

def hue_to_rgb(h):
    r =       abs(h * 6.0 - 3.0) - 1.0
    g = 2.0 - abs(h * 6.0 - 2.0)
    b = 2.0 - abs(h * 6.0 - 4.0)
    return saturate(r), saturate(g), saturate(b)

def hsl_to_rgb(h, s, l):
    r, g, b = hue_to_rgb(h)
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    r = (r - 0.5) * c + l
    g = (g - 0.5) * c + l
    b = (b - 0.5) * c + l
    return (r, g, b)

def gamma(encoded):
    return (ceil(pow(encoded[0], g_gamma)*g_brightness),
            ceil(pow(encoded[1], g_gamma)*g_brightness),
            ceil(pow(encoded[2], g_gamma)*g_brightness))

def gamma_2(encoded):
    return (ceil(encoded[0]*encoded[0]*g_brightness),
            ceil(encoded[1]*encoded[1]*g_brightness),
            ceil(encoded[2]*encoded[2]*g_brightness))

def shader_rgb1(time, x, y=0):
    # treat time in seconds as degrees of angle
#    assert(y == 0)
    angle = radians(time + x)*6.0 # map 60 seconds to full circle
    return ((1.0 + sin(angle*1.0))/2, (1.0 + sin(-angle*2.0))/2, (1.0 + sin(angle*3.0))/2)

def shader_hsl1(time, x, y=0):
    # hue ranges from 0 to 1 over the course of a minute, then wraps
    hue = (time + x) % 60.0 / 60.0
    return hsl_to_rgb(hue, 1.0, 0.5)

def grayscale1(time, x, y=0): # grey ramp
    return ((x / 59.0), (x / 59.0), (x / 59.0))

def render(shader, time, width, height=1):
#    print("time =", time)
    for i, c in enumerate(shader(time, x, y) for x in range(width) for y in range(height)):
        np[i] = gamma_2(c)
        
pwr = machine.Pin(PWR_PIN, machine.Pin.OUT)
led = machine.Pin(LED_PIN, machine.Pin.OUT)
pin = machine.Pin(NEOPIXEL_PIN, machine.Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, NUM_NEOPIXELS)   # create NeoPixel driver

pwr.value(0) # enable the NeoPixel output
start = time.ticks_ms() # get millisecond counter
loop_prev = start
render_max = 0
while True:
    loop_start = time.ticks_ms()
    delta = time.ticks_diff(loop_start, start)/1000.0 # compute time difference in seconds
    #print("delta_secs =", delta_secs)
    loop_prev = loop_start
    render(shader_hsl1, delta, len(np))
    np.write()
    render_time = time.ticks_diff(time.ticks_ms(), loop_start)
    if render_time > render_max:
        render_max = render_time
        print("render time =", render_time, "ms")
    assert(render_time < 65)
    time.sleep_ms(100 - render_time)

