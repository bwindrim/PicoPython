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

# Configure the number of WS2812 LEDs, pins and brightness.
NUM_NEOPIXELS = 60 # ItsyBitsy RP2040 only has one neopixel
PWR_PIN = 17      # GPIO17 is the 74AHCT125N output 4 enable (active low)
NEOPIXEL_PIN = 16 # GPIO16 on Pico breadboard
LED_PIN = "LED"   # let MicroPython decide which pin controls the on-board LED

def pixel_value(color, brightness):
        r = int(color[0] * brightness)
        g = int(color[1] * brightness)
        b = int(color[2] * brightness)
        return (r, g, b)
    
def pixels_fill(rgb, brightness):
    r = int(rgb[0] * brightness)
    g = int(rgb[1] * brightness)
    b = int(rgb[2] * brightness)
    for i in range(len(np)):
        np[i] = (g, r, b)
 
def pixels_shift_append(rgb, brightness):
    grb = (rgb[1], rgb[0], rgb[2])
    for i in range(len(np) - 1):
        np[i] = np[i + 1]
    np[len(np) - 1] = grb
   
pwr = machine.Pin(PWR_PIN, machine.Pin.OUT)
led = machine.Pin(LED_PIN, machine.Pin.OUT)
pin = machine.Pin(NEOPIXEL_PIN, machine.Pin.OUT)   # set GPIO0 to output to drive NeoPixels
np = NeoPixel(pin, NUM_NEOPIXELS)   # create NeoPixel driver

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
rgb = WHITE
color = "FFFFFF"

pwr.value(0) # enable the NeoPixel output

brightness = 1.0
pixels_fill(BLACK, brightness)

# WLAN setup
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

# Set up HTTP listen socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(True)

print('listening on', addr)
led_value = 0

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
#        print('client connected from', addr)
        buffer = cl.recv(1024)
#        print(buffer)

        request = buffer.decode("utf-8")
        req_list = request.split()
        assert(len(req_list) >= 2)
        cmd = req_list.pop(0)
        
        if cmd == "GET": # http GET request
            path_list = req_list.pop(0).split('/')
#            print("path_list =", path_list)
            path_list.pop(0) # discard empty first element
            path_head = path_list.pop(0)
            response = "\r\n"
            
            if (path_head == "light"):
                attr = path_list.pop(0)
                
                if attr == 'on':
                    print("led on")
                    led_value = brightness
                    pixels_fill(rgb, led_value)
                    np.write()              # write data to all pixels

                if attr == 'off':
                    print("led off")
                    led_value = 0.0
                    pixels_fill(rgb, led_value)
                    np.write()              # write data to all pixels
                    
                if attr == 'set':
                    color = path_list[0]
                    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
                    print("Set colour to:", color, "RGB =", rgb)
                    pixels_fill(rgb, led_value)
                    np.write()              # write data to all pixels

                if attr == 'bright':
                    print("Query brightness:", brightness*100)
                    response = str(brightness*100) + "\r\n"

                if attr == 'color':
                    print("Query color:", color)
                    response = str(color) + "\r\n"
                    
                if attr == 'status':
                    print("Query status:", led_value)
                    response = str(led_value) + '\r\n'

#        print ("response =", response)
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()

    except OSError as e:
        cl.close()
        print('connection closed')
     
