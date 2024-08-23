# This example reads the voltage from a LiPo battery connected to Pimoroni Pico LiPo
# and uses this reading to calculate how much charge is left in the battery.
# It then displays the info on the screen of Pico Display (or Pico Display 2.0).
# With Pimoroni Pico LiPo, you can read the battery percentage while it's charging.
# Save this code as main.py on your Pico if you want it to run automatically!

from machine import ADC, Pin
import time

led = Pin("LED", Pin.OUT)

vsys = ADC(29)                      # reads the system input voltage
charging = Pin(24, Pin.IN)          # reading GP24 tells us whether or not USB power is connected
conversion_factor = 3 * 3.3 / 65535

full_battery = 4.2                  # reference voltages for a full/empty battery, in volts
empty_battery = 2.8                 # the values could vary by battery size/manufacturer so you might need to adjust them

while True:
    led.toggle()
    # convert the raw ADC read into a voltage, and then a percentage
    voltage = vsys.read_u16() * conversion_factor
    percentage = 100 * ((voltage - empty_battery) / (full_battery - empty_battery))
    if percentage > 100:
        percentage = 100

    if charging.value() == 1:         # if it's plugged into USB power...
        print("Charging!")
    else:                             # if not, display the battery stats
        print('{:.2f}'.format(voltage) + "v", '{:.0f}%'.format(percentage))

    time.sleep(0.5)
