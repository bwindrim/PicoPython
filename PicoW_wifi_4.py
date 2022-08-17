import time
import network
import socket
import machine
import rp2
import ubinascii

ssids = {
    'BedroomTestNetwork': 'dvdrtsPnk4xq'
    }

led = machine.Pin("LED", machine.Pin.OUT)
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

html = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W</h1>
        <p>%s</p>
    </body>
</html>
"""

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

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        print('client connected from', addr)
        request = cl.recv(1024)
        print(request)

        request = str(request)
        led_on = request.find('/light/on')
        led_off = request.find('/light/off')
        query_status = request.find('/light/status')
        print( 'led on = ' + str(led_on))
        print( 'led off = ' + str(led_off))
        response = ""

        if led_on == 6:
            print("led on")
            led.value(1)
            stateis = "LED is ON"
            response = html % stateis

        if led_off == 6:
            print("led off")
            led.value(0)
            stateis = "LED is OFF"
            response = html % stateis

        if query_status == 6:
            print("status =", led.value())
            response = str(led.value()) + '\r\n'

        print ("response =", response)
        cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
        cl.send(response)
        cl.close()

    except OSError as e:
        cl.close()
        print('connection closed')