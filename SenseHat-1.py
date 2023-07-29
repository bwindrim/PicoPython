from machine import I2C, SoftI2C, Pin
import framebuf

# ItsyBitsy RP2040 wires its SDA and SCL to GPIO2 and GPIO3 respectively, which are connected to I2C1
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)

#print (i2c.scan())
fb = bytearray(128)
buf = bytearray(192)
fbuf = framebuf.FrameBuffer(fb, 8, 8, framebuf.RGB565)

def pixel(arr, x, y):
    "Extract a pixel x,y from the specified framebuffer bytearray and return it, with its co-ordinates"
    n = 2*(x + 8*y)
    lo = arr[n]
    hi=arr[n+1]
    return lo + (hi << 8), x, y

def update(i2c, buff, fb):
    "Copy a MicroPython framebuffer bytearray to an I2C buffer, and write it to the device"
    for i, (p,x,y) in enumerate(pixel(fb, x, y) for y in range(8) for x in range(8)):
        # extract the RGB components froma 16-bit pixel
        red = p >> 11
        green = 0x2f & (p >> 5)
        blue = p & 0x1f
        # and write them (as 6-bit values) to an I2C bytearray
        buf[x + 24*y] = red << 1
        buf[x + 24*y + 8] = green
        buf[x + 24*y + 16] = blue << 1
    # send the bytearray to the I2C LED grid
    i2c.writeto_mem(0x46, 0, buf)

fbuf.fill(0x2f << 11)
fbuf.text('Y',0, 0, 0xffff)
update(i2c, buf, fb)
