import time
import network
import machine
import rp2
import ubinascii

led = machine.Pin("LED", machine.Pin.OUT)
rp2.country('GB')

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

mac = ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
print("mac address = ", mac)
wlan_scan = wlan.scan()
for net in wlan_scan:
    print(net)
wlan.connect('Ardfern Motorhome Park', 'ARDFERNMP')

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
