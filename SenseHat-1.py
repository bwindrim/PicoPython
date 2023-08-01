from machine import I2C, SoftI2C, Pin
import framebuf
import time

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
    "Copy a MicroPython framebuffer bytearray to an I2C buffer, and write it to the device"
    buf = bytearray(192) # space for 8x8 LED array, 3 bytes per LED
    n = 2*(x_offset + width*y_offset) # calculate the first pixel address
    for y in range(8):
        for x in range(8):
            # Extract a 16-bit pixel (x,y) from the specified framebuffer bytearray
            pix = fb[n] + (fb[n+1] << 8)  # combine the lo and hi bytes into a 16-bit pixel
            # Write the RGB components from the 16-bit pixel (as 6-bit values) to an I2C bytearray
            pos = of[dir] + xf[dir]*x + yf[dir]*y
            buf[pos]      = (pix >> 11) << 1
            buf[pos + 8]  = 0x2f & (pix >> 5)
            buf[pos + 16] = (pix & 0x1f) << 1
            n += 2
        n += width + width - 16
    # send the bytearray to the I2C LED grid
    i2c.writeto_mem(0x46, 0, buf)

string = "Hello World!"
w = 8*(len(string) + 2)

fbuf, fb = create_framebuffer(width=w, height=16)

fbuf.fill(0x2f << 11)
fbuf.text(string, 8, 0, 0xffff)

for dir in range(4):
    for offset in range(8*(1 + len(string))):
        update(i2c, fb, x_offset=offset, y_offset=0, width=w, dir=dir)
        time.sleep(0.025)

    

