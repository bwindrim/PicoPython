import array, time
from machine import Pin
import rp2
 
# Configure the number of WS2812 LEDs, pins and brightness.
NUM_NEOPIXELS = 4 # ItsyBitsy RP2040 only has one neopixel
#PWR_PIN = 16      # GPIO16 is neopixel power on ItsyBitsy RP2040
NEOPIXEL_PIN = 20 # GPIO17 is the neopixel control on ItsyBitsy RP2040, 20 on Pico 2 breadboard
LED_PIN = "LED"      # GPIO11 is the red LED on ItsyBitsy RP2040, GPIO25 for Pico, "LED" is generic name for on-board LED on many boards

#pwr = Pin(PWR_PIN, Pin.OUT)
led = Pin(LED_PIN, Pin.OUT)
npx = Pin(NEOPIXEL_PIN, Pin.OUT)
 
# RP2040 PIO state machine program for outputting to neopixels.
# Each iteration of the PIO loop outputs one bit to the neopixel chain and
# takes 8 state machine cycles, whether outputting a 1 or a 0.
# So at a state machine clock frequency of 8MHz (see below) this gives
# the 1MHz bitrate that (some) neopixels seem to tolerate.
@rp2.asm_pio(sideset_init=(rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW), out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    "RP2040 PIO state machine program for outputting to neopixels, 3 sideset pins"
    T1 = 2 # number of cycles for which to hold high for any bit
    T2 = 2 # number of cycles for which to output bit value
    T3 = 4 # number of cycles for which to hold low for any bit
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0b000)    [T3 - 1] # all low for 4 cycles
    jmp(not_x, "do_zero")   .side(0b111)    [T1 - 1] # all high for 2 cycles
    jmp("bitloop")          .side(0b111)    [T2 - 1] # all high for 2 cycles = '1'
    label("do_zero")
    nop()                   .side(0b000)    [T2 - 1] # all low for 2 cycles = '0'
    wrap()
 
 
 
# Create the StateMachine with the ws2812 program, running at a clock frequency of 8MHz,
# and outputting on the neopixel pin.
sm0 = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=npx)
 
# Start the StateMachine, it will wait for data on its FIFO.
sm0.active(True)
 
# Display a pattern on the LEDs via an array of LED RGB values.
ar = array.array("I", [0 for _ in range(NUM_NEOPIXELS)])

def pixels_show(ar):
    # Push the word onto the state machine’s TX FIFO, discarding the leftmost byte
    sm0.put(ar, 8)
    # The data line must be held low for a minimum of 300 microseconds
    # for the new colors to “latch”
    time.sleep_ms(10)

def pixel_value(color, brightness):
        r = int(color[0] * brightness)
        g = int(color[1] * brightness)
        b = int(color[2] * brightness)
        return (r << 16) + (g << 8) + b # on-board neopixel uses GRB, rather than RGB
    
def pixels_fill(color, brightness):
    for i in range(len(ar)):
        ar[i] = pixel_value(color, brightness)
 
def pixels_shift_append(color, brightness):
    for i in range(len(ar) - 1):
        ar[i] = ar[i + 1]
    ar[len(ar) - 1] = pixel_value(color, brightness)
   
    
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

led.value(0) # turn off the board's own LED initially
#pwr.value(1) # turn on power to the neopixel

brightness = 0.1
pixels_fill(BLACK, brightness)

try:
    while True:
        for color in COLORS:
            #pixels_fill(color, brightness)
            pixels_shift_append(color, brightness)
            pixels_show(ar)
            time.sleep(0.5)
            led.toggle() # blink the LED
except KeyboardInterrupt:
    pixels_fill(BLACK, brightness)
    pixels_show(ar)
    led.value(1) # show we're still powered
    print("Done")
