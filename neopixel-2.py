from machine import Pin
from neopixel import NeoPixel
import time

# Configure the number of WS2812 LEDs, pins and brightness.
NUM_NEOPIXELS = 1 # ItsyBitsy RP2040 only has one neopixel
#PWR_PIN = 1      # GPIO16 is neopixel power on ItsyBitsy RP2040
NEOPIXEL_PIN = 16 # GPIO17 is the neopixel control on ItsyBitsy RP2040, 16 on Pico breadboard
LED_PIN = 25      # GPIO11 is the red LED on ItsyBitsy RP2040, GPIO25 for Pico

#pwr = Pin(PWR_PIN, Pin.OUT)
led = Pin(LED_PIN, Pin.OUT)
#npx = Pin(NEOPIXEL_PIN, Pin.OUT)
 
def pixel_value(color, brightness):
        r = int(color[0] * brightness)
        g = int(color[1] * brightness)
        b = int(color[2] * brightness)
        return (r, g, b)
    
def pixels_fill(color, brightness):
    for i in range(len(np)):
        np[i] = pixel_value(color, brightness)
 
def pixels_shift_append(color, brightness):
    for i in range(len(np) - 1):
        np[i] = np[i + 1]
    np[len(np) - 1] = pixel_value(color, brightness)
   
    

pin = Pin(NEOPIXEL_PIN, Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, 3)   # create NeoPixel driver on GPIO16 for 3 pixels
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

brightness = 0.5
pixels_fill(BLACK, brightness)

while True:
    for color in COLORS:
        #pixels_fill(color, brightness)
        pixels_shift_append(color, brightness)
        np.write()              # write data to all pixels
        time.sleep(0.5)
        led.toggle() # blink the red LED
        
# np[0] = (127, 0, 0) # set the first pixel to white
# np[1] = (0, 127, 0) # set the first pixel to white
# np[2] = (0, 0, 127) # set the first pixel to white
# np.write()              # write data to all pixels
# r, g, b = np[0]         # get first pixel colour
