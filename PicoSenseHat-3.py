from machine import I2C, SoftI2C, Pin, PWM
import math, time
import framebuf
import asyncio
import sys
import gamepad

class SenseHat:
    "Wrapper class for accessing the Sense Hat"
    
    def __init__(self, i2c_pin_no_clk=3, i2c_pin_no_data=2):
        # ItsyBitsy RP2040 wires its SDA and SCL to GPIO2 and GPIO3 respectively, which are connected to I2C1
        self.i2c = I2C(1, scl=Pin(i2c_pin_no_clk), sda=Pin(i2c_pin_no_data), freq=400000)

    def create_framebuffer(self, width=8, height=8):
        "Allocate a bytearray of the required size and then create a MicroPython framebuffer"
        pixel_size = 2 # assume 16-bit pixels, for now
        pix_format = framebuf.RGB565
        self.fb = bytearray(width*height*pixel_size)
        self.fbuf = framebuf.FrameBuffer(self.fb, width, height, pix_format)

    # Rotation constants
    xf = [1, 24, -1, -24]
    yf = [24, -1, -24, 1]
    of = [0, 7, 7*25, 7*24]

    def update(self, x_offset=0, y_offset=0, width=8, dir=0):
        "Copy a MicroPython framebuffer bytearray to an intermediate buffer, and write it to the I2C device"
        buf = bytearray(192) # space for 8x8 LED array, 3 bytes per LED
        src = 2*(x_offset + width*y_offset) # calculate the first pixel address
        for y in range(8):
            for x in range(8):
                # Extract a 16-bit pixel (x,y) from the specified framebuffer bytearray
                pix = self.fb[src] + (self.fb[src+1] << 8)  # combine the lo and hi bytes into a 16-bit pixel
                # Apply rotation to calculate destination offset
                dst = SenseHat.of[dir] + SenseHat.xf[dir]*x + SenseHat.yf[dir]*y
                # Write the RGB components from the 16-bit pixel (as 6-bit values) to an I2C bytearray
                buf[dst]      = (pix >> 11) << 1  # red
                buf[dst + 8]  = 0x2f & (pix >> 5) # green
                buf[dst + 16] = (pix & 0x1f) << 1 # blue
                src += 2
            src += width + width - 16
        # send the bytearray to the I2C LED grid
        self.i2c.writeto_mem(0x46, 0, buf)

    def read_stick(self):
        "Read state of Sense Hat joystick, causes LEDs to flicker"
        b = self.i2c.readfrom_mem(0x46,0xf2,1) # read joystick
        
        return int.from_bytes(b, 'little')

class L9110():
    def __init__(self, IA=18, IB=19, pwm_rate=20000):
        # Create a pair of PWMOut objects for each motor channel.
        self.ia = PWM(Pin(IA))
        self.ia.freq(pwm_rate)
        self.ia.duty_u16(0)
        self.ib = PWM(Pin(IB))
        self.ib.freq(pwm_rate)
        self.ib.duty_u16(0)

    def write(self, rate):
        """Set the speed and direction on a single motor channel.

        :param rate: modulation value between -1.0 and 1.0, full reverse to full forward."""

        # convert the rate into a 16-bit fixed point integer
        pwm = min(max(int(2**16 * abs(rate)), 0), 65535)
        print("pwm =", pwm)
        if rate < 0:
            self.ia.duty_u16(0)
            self.ib.duty_u16(pwm)
        else:
            self.ib.duty_u16(0)
            self.ia.duty_u16(pwm)

def write_motors(motors, duty=0.0):
    for motor in motors:
        motor.write(duty)


#--------------------------------------------------------------------------------
# Create an object to represent a motor driver.
print("Creating driver objects")
motor0 = L9110(IA=12, IB=13)
motor1 = L9110(IA=14, IB=15)
motor2 = L9110(IA=16, IB=17)
motor3 = L9110(IA=18, IB=19)

motors = [motor0, motor1, motor2, motor3]

string = "Hello World!"
w = 8*(len(string) + 2)

hat = SenseHat()
hat.create_framebuffer(width=w)

hat.fbuf.fill(0x2f << 11)
hat.fbuf.text(string, 8, 0, 0xffff)

async def main():
    write_motors(motors, duty=0.0)
    gamepad.start()
    last = None
    last_identity = None
    while True:
        gamepad.poll()
        info = gamepad.info()
        identity = (info["name"], info["address"], info["vendor_id"],
                    info["product_id"], info["transport"], info["ready"])
        if identity != last_identity:
            print("DEVICE", info)
            last_identity = identity
        current = (gamepad.status(), gamepad.read())
        if current != last:
            print("STATE", current, "reports", info["reports"])
            last = current
        pad = gamepad.read() # note: this causes the LEDs to flicker
        joy = pad[1]

        write_motors(motors, duty=pad[4]/512.0)
        
        if joy:
            if joy & 0x1:
                dir = 1
            elif joy & 0x2:
                dir = 0
            elif joy & 0x4:
                dir = 3
            elif joy & 0x8:
                dir = 2
            elif joy & 0x10:
                sys.exit()
            print("joy =", joy, "dir =", dir)
            for offset in range(8*(1 + len(string))):
                hat.update(x_offset=offset, width=w, dir=dir)
                await asyncio.sleep_ms(25)

        await asyncio.sleep_ms(5)


asyncio.run(main())
