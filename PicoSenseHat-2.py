import time
from machine import I2C, SoftI2C, Pin
import framebuf
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
NUM_PIXELS = 64 
np = [BLACK] * NUM_PIXELS

g_gamma = 2.2
g_brightness = 63.0*pow(0.5, g_gamma) # global brightness setting, range 0.0 - 63.0

# def hue_to_rgb(h):
#     r =       abs(h * 6.0 - 3.0) - 1.0
#     g = 2.0 - abs(h * 6.0 - 2.0)
#     b = 2.0 - abs(h * 6.0 - 4.0)
# #    return saturate(r), saturate(g), saturate(b)
#     return max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b))

def hsl_to_rgb(h, s, l):
    # calculate r, g, &b weightings from hue
    r =       abs(h * 6.0 - 3.0) - 1.0
    g = 2.0 - abs(h * 6.0 - 2.0)
    b = 2.0 - abs(h * 6.0 - 4.0)
    # clamp the weightings to the normalised range (0-1)
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    # apply saturation and luminance to the colour mix
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    r = (r - 0.5) * c + l
    g = (g - 0.5) * c + l
    b = (b - 0.5) * c + l
    return (r, g, b)

def gamma(encoded):
    return (ceil(pow(encoded[0], g_gamma)*g_brightness),
            ceil(pow(encoded[1], g_gamma)*g_brightness),
            ceil(pow(encoded[2], g_gamma)*g_brightness))

# Fixed gamma 2.0 function - doesn't save much time wrt. gamma()
def gamma_2(encoded):
    return (ceil(encoded[0]*encoded[0]*g_brightness),
            ceil(encoded[1]*encoded[1]*g_brightness),
            ceil(encoded[2]*encoded[2]*g_brightness))

def shader_rgb1(time, x, y):
    # treat time in seconds as degrees of angle
#    assert(y == 0)
    angle = radians(time + x)*6.0 # map 60 seconds to full circle
    return ((1.0 + sin(angle*1.0))/2, (1.0 + sin(-angle*2.0))/2, (1.0 + sin(angle*3.0))/2)

def shader_hsl1(time, x, y):
    # hue ranges from 0 to 1 over the course of eight seconds, then wraps
    hue = (time + x) % 8.0 / 8.0
    sat = (1.0 + y) / 16.0
    return hsl_to_rgb(hue, 1.0, sat)

def shader_hsl2(time, x, y):
    # saturation ranges from 0 to 1 over the course of a minute, then wraps
    s = time % 60.0 / 60.0
    return hsl_to_rgb(2/3, s, x/59.0)

def shader_hsl3(time, x, y):
    # hue ranges from 0 to 1 over the course of a minute, then wraps
#    print("x =", x, "y =", y)
    hue = (time*20 + x) % 15.0 / 15.0
    return hsl_to_rgb(hue, 1.0, (y + 1) / 8)

def grayscale1(time, x, y): # grey ramp
    return ((x / 59.0), (x / 59.0), (x / 59.0))

def render(shader, gamma, time, width, height=1):
#    print("time =", time)
    for i, c in enumerate(shader(time, x, y) for y in range(height) for x in range(width)):
        np[i] = gamma(c)
        
# ItsyBitsy RP2040 wires its SDA and SCL to GPIO2 and GPIO3 respectively, which are connected to I2C1
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)

def create_framebuffer(width=8, height=8):
    "Allocate a bytearray of the required size and then create a MicroPython framebuffer"
    pixel_size = 2 # assume 16-bit pixels, for now
    pix_format = framebuf.RGB565
    fb = bytearray(width*height*pixel_size)
    fbuf = framebuf.FrameBuffer(fb, width, height, pix_format)
    return fbuf, fb

# Rotation constants
xf = [1, 24, -1, -24]
yf = [24, -1, -24, 1]
of = [0, 7, 7*25, 7*24]

def update(i2c, fb, x_offset=0, y_offset=0, width=8, dir=0):
    "Copy a MicroPython framebuffer bytearray to an intermediate buffer, and write it to the I2C device"
    buf = bytearray(192) # space for 8x8 LED array, 3 bytes per LED
    src = 2*(x_offset + width*y_offset) # calculate the first pixel address
    for y in range(8):
        for x in range(8):
            # Extract a 16-bit pixel (x,y) from the specified framebuffer bytearray
            pix = fb[src] + (fb[src+1] << 8)  # combine the lo and hi bytes into a 16-bit pixel
            # Apply rotation to calculate destination offset
            dst = of[dir] + xf[dir]*x + yf[dir]*y
            # Write the RGB components from the 16-bit pixel (as 6-bit values) to an I2C bytearray
            buf[dst]      = (pix >> 11) << 1  # red
            buf[dst + 8]  = 0x2f & (pix >> 5) # green
            buf[dst + 16] = (pix & 0x1f) << 1 # blue
            src += 2
        src += width + width - 16
    # send the bytearray to the I2C LED grid
    i2c.writeto_mem(0x46, 0, buf)

def rgb16(rgb):
    (red, green, blue) = rgb # unpack the tuple
    assert(red <= 63)
    assert(green <= 63)
    assert(blue <= 63)

    return (red&0x1F) << 11 | (green&0x3F) << 5 | (blue&0x1F)
    
def set_pixels(np):
    i = 0
    for y in range(8):
        for x in range(8):
            fbuf.pixel(x, y, rgb16(np[i]))
            i += 1
        
fbuf, fb = create_framebuffer(width=8, height=8)
    
start = time.ticks_ms() # get millisecond counter
loop_prev = start
render_max = 0
while True:
    loop_start = time.ticks_ms()
    delta = time.ticks_diff(loop_start, start)/1000.0 # compute time difference in seconds
    #print("delta =", delta)
    loop_prev = loop_start
    render(shader_hsl1, gamma, delta, 8, 8)
    set_pixels(np)
    update(i2c, fb, x_offset=0, y_offset=0, width=8, dir=0)
    render_time = time.time()*1000.0 - loop_start
    if render_time > render_max:
        render_max = render_time
        print("render time =", render_time, "ms")
#    assert(render_time < 65)
   # time.sleep_ms(100 - render_time)

