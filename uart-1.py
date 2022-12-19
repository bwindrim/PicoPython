from machine import Pin, UART

uart0 = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))