### main.py
import time
import picosleep
from machine import Pin, RTC, ADC
from i2c_responder import I2CResponder
from struct import pack, unpack

adc = ADC(Pin(28)) # main battery voltage measurement
rtc = RTC()
pwr = Pin(22, Pin.OUT, value=1) # wide-input enable, high for power on
led = Pin(25, Pin.OUT, value=1)

# When using ADC pins for I2C we need to turn on the pull-ups
Pin(26,  Pin.IN, Pin.PULL_UP) # enable internal pull-up resistor
Pin(27,  Pin.IN, Pin.PULL_UP) # enable internal pull-up resistor
i2c_responder = I2CResponder(1, sda_gpio=26, scl_gpio=27, responder_address=0x41)

status = 0x42
do_prt = False

def sleep(interval_s):
    ""
    reason = 0 #wake_reason()
    if do_prt:
        print("Sleeping for", interval_s, "s...")
    time.sleep(1) # allow messages to get out before we stop the clocks
    while interval_s > 0:
        led.off()
        if do_prt:
            time.sleep(1)
        else:
            picosleep.seconds(2)
        led.on()
        time.sleep_ms(10)
        interval_s -= 1
    time.sleep(4)
    if do_prt:
        print("...wakeup, reason =", reason)
    return reason

try:
    print("Polling I2C")
    prefix_reg = 0
    # All times are in milliseconds(?)
    ticks_base = time.ticks_ms()
    ticks_timeout = 5000
    sleep_interval = 5
    sleep(sleep_interval)
    while True:
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
        if ticks_timeout != 0 and ticks_interval >= ticks_timeout: # timeout set and reached
            # This is where we would cut the power to the Pi
            if do_prt:
                print("Watchdog timeout exceeded: timeout =", ticks_timeout, "interval =", ticks_interval);
            #sleep(sleep_interval)
            ticks_base = ticks_now
            
except KeyboardInterrupt:
    pass
