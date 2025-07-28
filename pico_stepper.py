#!/usr/bin/python
#--------------------------------------
#    ___  ___  _ ____          
#   / _ \/ _ \(_) __/__  __ __ 
#  / , _/ ___/ /\ \/ _ \/ // / 
# /_/|_/_/  /_/___/ .__/\_, /  
#                /_/   /___/   
#
#    Stepper Motor Test
#
# A simple script to control
# a stepper motor.
#
# Author : Matt Hawkins
# Date   : 28/09/2015
#
# http://www.raspberrypi-spy.co.uk/
#
#--------------------------------------

# Import required libraries
from machine import Pin, Timer
import time

led = Pin('LED', Pin.OUT)
timer = Timer()

pins = {}

def GPIO_setup(list, dir):
    "Initialise a list of GPIOs"
    for i in list:
        pin = Pin(i, dir)
        pins[i] = pin

def GPIO_output(list, values):
    "Set one or more GPIOs to one or more values"
    for (i,j) in zip(list, values):
        pins[i].value(j)
    
# Define GPIO signals to use
# Physical pins 11,15,16,18
# GPIO17,GPIO22,GPIO23,GPIO24
#StepPins = [16,2,17,3] # motor 0
#StepPins = [4,6,5,7] # motor 1
#StepPins = [8,10,9,11] # motor 2
#StepPins = [12,14,13,15] # motor 3
StepPins = [16,2,17,3] # motor 3

# Set all motor pins as outputs
GPIO_setup(StepPins, Pin.OUT)
# and set to off
GPIO_output(StepPins, [0, 0, 0, 0])

# Define advanced sequence
# as shown in manufacturer's datasheet
Seq = [[1,0,0,1],
       [1,0,0,0],
       [1,1,0,0],
       [0,1,0,0],
       [0,1,1,0],
       [0,0,1,0],
       [0,0,1,1],
       [0,0,0,1]]
       
StepCount = len(Seq)
StepDir = 1 # Set to 1 or 2 for clockwise
            # Set to -1 or -2 for anti-clockwise

# Read wait time from command line
# if len(sys.argv)>1:
#     WaitTime = int(sys.argv[1])/float(1000)
# else:
WaitTime = 20/float(1000)

# Initialise variables
StepCounter = 0

try:
    print("Running, WaitTime = ", WaitTime, "s")
    # Start main loop
    while True:

        led.toggle()

        GPIO_output(StepPins, Seq[StepCounter])

        # If we reach the end of the sequence
        # start again
        StepCounter = (StepCounter + StepDir) % StepCount

        # Wait before moving on
        time.sleep(WaitTime)
except KeyboardInterrupt:
    print ("Done.")
    GPIO_output(StepPins, [0, 0, 0, 0])
    # and set to input
    GPIO_setup(StepPins, Pin.IN)
    
