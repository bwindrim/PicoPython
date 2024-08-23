# This example shows how to read the voltage from a LiPo battery connected to a Raspberry Pi Pico via our Pico Lipo SHIM
# and uses this reading to calculate how much charge is left in the battery.
# Remember to save this code as main.py on your Pico if you want it to run automatically!

from machine import ADC, Pin
import time

import network

led = Pin("LED", Pin.OUT)

def get_vsys():
    conversion_factor = 3 * 3.3 / 65535
    wlan = network.WLAN(network.STA_IF)
    wlan_active = wlan.active()

    try:
        # Don't use the WLAN chip for a moment.
        wlan.active(False)

        # Make sure pin 25 is high.
        Pin(25, mode=Pin.OUT, pull=Pin.PULL_DOWN).high()
        
        # Reconfigure pin 29 as an input.
        Pin(29, Pin.IN)
        
        vsys = ADC(29)
        return vsys.read_u16() * conversion_factor

    finally:
        # Restore the pin state and possibly reactivate WLAN
        Pin(29, Pin.ALT, pull=Pin.PULL_DOWN, alt=7)
        wlan.active(wlan_active)

#vsys = ADC(29)                      # reads the system input voltage
charging = Pin("WL_GPIO2", Pin.IN)          # reading GP24 tells us whether or not USB power is connected
conversion_factor = 3 * 3.3 / 65535

full_battery = 4.2                  # these are our reference voltages for a full/empty battery, in volts
empty_battery = 2.8                 # the values could vary by battery size/manufacturer so you might need to adjust them

while True:
    led.toggle()
    # convert the raw ADC read into a voltage, and then a percentage
    voltage = get_vsys() #vsys.read_u16() * conversion_factor
    percentage = 100 * ((voltage - empty_battery) / (full_battery - empty_battery))
    if percentage > 100:
        percentage = 100.00

    if charging.value() == 1:         # if it's plugged into USB power...
        print("Charging!")
    else:                             # if not, display the battery stats
        print('{:.2f}'.format(voltage) + "v", '{:.0f}%'.format(percentage))

    time.sleep(0.5)
