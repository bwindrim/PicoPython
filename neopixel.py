import array, time
from machine import Pin
import rp2
 
# Configure the number of WS2812 LEDs, pins and brightness.
NUM_NEOPIXELS = 3 # ItsyBitsy RP2040 only has one neopixel
#PWR_PIN = 16      # GPIO16 is neopixel power on ItsyBitsy RP2040
NEOPIXEL_PIN = 16 # GPIO17 is the neopixel control on ItsyBitsy RP2040, 16 on Pico breadboard
LED_PIN = 25      # GPIO11 is the red LED on ItsyBitsy RP2040, GPIO25 for Pico

#pwr = Pin(PWR_PIN, Pin.OUT)
led = Pin(LED_PIN, Pin.OUT)
npx = Pin(NEOPIXEL_PIN, Pin.OUT)
 
# RP2040 PIO state machine program for outputting to neopixels.
# Each iteration of the PIO loop outputs one bit to the neopixel chain and
# takes 10 state machine cycles, whether outputting a 1 or a 0.
# So at a state machine clock frequency of 8MHz (see below) this gives
# the 800KHz bitrate that neopixels require.
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    "RP2040 PIO state machine program for outputting to neopixels"
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1] # low for 3 cycles
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1] # high for 2 cycles
    jmp("bitloop")          .side(1)    [T2 - 1] # high for 5 cycles = '1'
    label("do_zero")
    nop()                   .side(0)    [T2 - 1] # low for 5 cycles = '0'
    wrap()
 
 
 
# Create the StateMachine with the ws2812 program, running at a clock frequency of ~cd get8MHz,
# and outputting on the neopixel pin.
sm0 = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=npx)
 
# Start the StateMachine, it will wait for data on its FIFO.
sm0.active(True)
 
# Display a pattern on the LEDs via an array of LED RGB values.
#ar = array.array("I", [0 for _ in range(NUM_NEOPIXELS)])
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

led.value(0) # turn off the red LED initially
#pwr.value(1) # turn on power to the neopixel

brightness = 0.1
pixels_fill(BLACK, brightness)

while True:
    for color in COLORS:
        #pixels_fill(color, brightness)
        pixels_shift_append(color, brightness)
        pixels_show(ar)
        time.sleep(0.5)
        led.toggle() # blink the red LED
