import time
import network
import socket
import machine
import rp2
import ubinascii
from neopixel import NeoPixel


ssids = {
    'BedroomTestNetwork': 'dvdrtsPnk4xq'
    }

led = machine.Pin("LED", machine.Pin.OUT)
# Configure the number of WS2812 LEDs, pins and brightness.
NUM_NEOPIXELS = 3 # ItsyBitsy RP2040 only has one neopixel
#PWR_PIN = 16      # GPIO16 is neopixel power on ItsyBitsy RP2040
NEOPIXEL_PIN = 16 # GPIO17 is the neopixel control on ItsyBitsy RP2040, 16 on Pico breadboard
LED_PIN = 25      # GPIO11 is the red LED on ItsyBitsy RP2040, GPIO25 for Pico

#pwr = Pin(PWR_PIN, Pin.OUT)
#led = machine.Pin(LED_PIN, Pin.OUT)
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
   
    

pin = machine.Pin(NEOPIXEL_PIN, machine.Pin.OUT)   # set GPIO0 to output to drive NeoPixels
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
color = BLACK

led.value(0) # turn off the red LED initially
#pwr.value(1) # turn on power to the neopixel

brightness = 0.1
pixels_fill(BLACK, brightness)

rp2.country('GB')

wlan = network.WLAN(network.STA_IF) # create a network object
wlan.active(True) # enable the network

mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
print("mac address = ", mac)

wlan_scan = wlan.scan() # get the list of accessible networks

for net in wlan_scan: # search the list of networks for one we have a password for
    print(net)
    ssid = net[0].decode("utf-8") # get the ssid as a string
    password = ssids.get(ssid)    # lookup the password
    print("ssid =", ssid, "password =", password)
    if None != password: # if we have a password then try to connect
        print("Connecting to:", ssid)
        wlan.connect(ssid, password)

# Wait for connect or fail
max_wait = 10
while max_wait > 0:
    wlan_status = wlan.status() # check what happened
    if wlan_status < 0 or wlan_status >= 3:
        break
    max_wait -= 1
    print("waiting for connection, failing in", max_wait, "seconds...")
    led.toggle()
    time.sleep(1)

if wlan_status == 3: # connected OK
    led.on()
    status = wlan.ifconfig()
    print("connected to:", wlan.config('essid'))
    print("channel     =", wlan.config('channel'))
#    print("essid       =", wlan.config('essid'))
    print("tx power    =", wlan.config('txpower'))
    print("ip addr     =", status[0] )
    print("subnet mask =", status[1] )
    print("gateway     =", status[2] )
    print("DNS server  =", status[3] )
else: # failed to connect
    led.off()  
    raise RuntimeError("network connection failed, status = " + str(wlan_status))

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)
led_value = 0

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024)
        print(request)

        request = request.decode("utf-8")
        led_on = request.find('/light/on')
        led_off = request.find('/light/off')
        query_status = request.find('/light/status')
        query_brightness = request.find('/light/bright')
        query_color = request.find('/light/color')
        response = "\r\n"

        if led_on == 6:
            print("led on")
            led_value = 1
            pixels_fill(WHITE, 100)
            np.write()              # write data to all pixels

        if led_off == 6:
            print("led off")
            led_value = 0
            pixels_fill(color, 0)
            np.write()              # write data to all pixels

        if query_brightness == 6:
            print("Query brightness")
            response = "100\r\n"

        if query_status == 6:
            print("status =", led_value)
            response = str(led_value) + '\r\n'

        print ("response =", response)
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()

    except OSError as e:
        cl.close()
        print('connection closed')
        
while True:
    for color in COLORS:
        #pixels_fill(color, brightness)
        pixels_shift_append(color, brightness)
        np.write()              # write data to all pixels
        time.sleep(0.5)
        led.toggle() # blink the red LED
        
