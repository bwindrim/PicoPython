### i2s_test3.py
import time
from machine import Pin, RTC, ADC, WDT, lightsleep
from i2c_responder import I2CResponder
from struct import pack, unpack

adc = ADC(Pin(28)) # main battery voltage measurement
rtc = RTC()
pwr = Pin(22, Pin.OUT, value=1) # wide-input enable, high for power on
led = Pin(25, Pin.OUT, value=1)
btn = Pin(12, Pin.IN, Pin.PULL_UP) # push-button input

# When using ADC pins for I2C we need to turn on the pull-ups
sda = Pin(26,  Pin.IN, Pin.PULL_UP) # enable internal pull-up resistor
scl = Pin(27,  Pin.IN, Pin.PULL_UP) # enable internal pull-up resistor
i2c_responder = I2CResponder(1, sda_gpio=26, scl_gpio=27, responder_address=0x41)

wdt = WDT(timeout=3000) # set a 2 second watchdog timeout

status = 0x42
watch_seconds = 40
wake_seconds = 20
do_prt = False

def pi_power_off():
    "Disable +5V power to the Pi by turning off the wide-input shim"
    pwr.off()
    led.off()
    # turn the pull-ups off to conserve power
#     sda.init(Pin.IN, None)
#     scl.init(Pin.IN, None)
    return

def pi_power_on():
    "Enable +5V power to the Pi by turning on the wide-input shim"
    pwr.on()
    led.on()
    # turn the pull-ups back on
#     sda.init(Pin.IN, Pin.PULL_UP)
#     scl.init(Pin.IN, Pin.PULL_UP)
    return

def suspend(interval_s):
    ""
    reason = 0x1 #wake_reason()
    if do_prt:
        print("Sleeping for", interval_s, "s...")
#    time.sleep(1) # allow messages to get out before we stop the clocks
    while interval_s > 0 and btn.value() is 1:
        wdt.feed() # the watchdog timer appears to keep running during lightsleep()
        if do_prt:
            time.sleep(1)
        else:
            lightsleep(998)
        led.on()
        time.sleep_ms(2)
        led.off()
        interval_s -= 1
#    time.sleep(4)
    if interval_s > 0:
        reason = 0x2 # button-press wakeup
    if do_prt:
        print("...wakeup, reason =", reason)
    return reason

reset_cause = machine.reset_cause()

if reset_cause is machine.PWRON_RESET:
    print("Power-on reset")
    status |= 0x10
else:
    assert(reset_cause is machine.WDT_RESET)
    print("Watchdog reset")
    status |= 0x20
    

try:
    print("Polling I2C")
    prefix_reg = 0
    # All times are in milliseconds(?)
    ticks_base = time.ticks_ms()
    ticks_timeout = 40000
#    sleep_interval = 20
#    suspend(1)
    while True:
        wdt.feed()
        # Poll for I2C writes
        if i2c_responder.write_data_is_available():
            buffer_in = i2c_responder.get_write_bytes(max_size=16)
            if len(buffer_in) >= 1:         # received some data
                prefix_reg = buffer_in[0]   # first byte must be a register number
                data = buffer_in[1:]        # copy the tail of the buffer
                if data: # buffer tail wasn't empty
                    if do_prt:
                        print("Received I2C WRITE: reg =", prefix_reg, "data =", data, "len =", len(data))
        # Poll for I2C reads                
        if i2c_responder.read_is_pending():
            if prefix_reg == 1: # status register + watchdog reset
                ticks_base = time.ticks_ms() # reset watchdog time base
                data = status.to_bytes(1, 'little')
                assert(len(data) == 1)
                if do_prt:
                    print("Status")
            elif prefix_reg == 2: # ADC value
                data = adc.read_u16().to_bytes(2,'little')
                assert(len(data) == 2)
                if do_prt:
                    print("ADC")
            elif prefix_reg == 3: # RTC date/time
                data = pack("HBBBBBBH", *rtc.datetime())
                assert(len(data) == 10)
                if do_prt:
                    print("RTC")
            elif prefix_reg == 4: # status register read and clear
                data = status.to_bytes(1, 'little')
                assert(len(data) == 1)
                status = 0
                if do_prt:
                    print("Status read and cleared")
            elif prefix_reg == 5: # watch time register (1 byte)
                data = watch_seconds.to_bytes(1, 'little')
                assert(len(data) == 1)
                status = 0
                if do_prt:
                    print("WATCH")
            elif prefix_reg == 6: # status register read and clear
                data = wake_seconds.to_bytes(2, 'little')
                assert(len(data) == 2)
                status = 0
                if do_prt:
                    print("WAKE")
            else: # return a zero byte for all unrecognised regs
                data = b'\x00'
                assert(len(data) == 1)
                if do_prt:
                    print("Default")
            i2c_responder.put_read_bytes(data)
            if do_prt:
                print("Sent I2C READ data for register", prefix_reg)
            prefix_reg = 0
            if do_prt:
                print()
        # Check for watchdog timeout
        ticks_now = time.ticks_ms()
        ticks_interval = time.ticks_diff(ticks_now, ticks_base)
        if watch_seconds != 0 and ticks_interval >= watch_seconds*1000: # timeout set and reached
            if do_prt:
                print("Watchdog timeout exceeded: timeout =", watch_seconds*1000, "interval =", ticks_interval);
            pi_power_off() # cut the power to the Pi
            status |= suspend(wake_seconds) # set the status from the wakeup reason
            pi_power_on() # restore power to the Pi
            ticks_base = time.ticks_ms()
            
except KeyboardInterrupt:
    pass
