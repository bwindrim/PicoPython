# MicroPython program for Raspberry Pi Pico to read MPU6050 (I2C0, addr 0x68)

import machine
import time

MPU6050_ADDR = 0x68

# MPU6050 Registers
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

# Init I2C0
# Use correct GPIOs for Pico I2C0: SDA=Pin 0, SCL=Pin 1
i2c = machine.I2C(0, scl=machine.Pin(1), sda=machine.Pin(0), freq=400_000)

# Wait for MPU6050 to be ready
time.sleep(0.1)

# Check if device is present before writing
devices = i2c.scan()
print("I2C devices found:", [hex(d) for d in devices])
if MPU6050_ADDR not in devices:
    raise RuntimeError("MPU6050 not found on I2C bus. Check wiring and address.")

# Wake up MPU6050
try:
    i2c.writeto_mem(MPU6050_ADDR, PWR_MGMT_1, b'\x00')
except OSError as e:
    print("Failed to write to MPU6050 PWR_MGMT_1 register:", e)
    print("Check power, wiring, and that SDA/SCL are not swapped.")
    raise

def read_word(reg):
    try:
        high = i2c.readfrom_mem(MPU6050_ADDR, reg, 1)[0]
        low  = i2c.readfrom_mem(MPU6050_ADDR, reg+1, 1)[0]
    except OSError as e:
        print("I2C read error at register 0x{:02X}: {}".format(reg, e))
        return 0
    val = (high << 8) | low
    if val & 0x8000:
        val -= 65536
    return val

def read_accel_gyro():
    ax = read_word(ACCEL_XOUT_H)
    ay = read_word(ACCEL_XOUT_H + 2)
    az = read_word(ACCEL_XOUT_H + 4)
    gx = read_word(GYRO_XOUT_H)
    gy = read_word(GYRO_XOUT_H + 2)
    gz = read_word(GYRO_XOUT_H + 4)
    return (ax, ay, az, gx, gy, gz)

while True:
    ax, ay, az, gx, gy, gz = read_accel_gyro()
    print('Accel: x={:6d} y={:6d} z={:6d} | Gyro: x={:6d} y={:6d} z={:6d}'.format(ax, ay, az, gx, gy, gz))
    time.sleep(0.5)
