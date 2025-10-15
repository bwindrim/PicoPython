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
i2c = machine.I2C(0, scl=machine.Pin(5), sda=machine.Pin(4), freq=400_000)

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

def calibrate(samples=100):
    print("Calibrating MPU6050... Please keep the device still.")
    sum_ax = sum_ay = sum_az = sum_gx = sum_gy = sum_gz = 0
    for _ in range(samples):
        ax, ay, az, gx, gy, gz = read_accel_gyro()
        sum_ax += ax
        sum_ay += ay
        sum_az += az
        sum_gx += gx
        sum_gy += gy
        sum_gz += gz
        time.sleep(0.01)
    offset_ax = sum_ax // samples
    offset_ay = sum_ay // samples
    offset_az = (sum_az // samples) - 16384  # 1g offset for Z
    offset_gx = sum_gx // samples
    offset_gy = sum_gy // samples
    offset_gz = sum_gz // samples
    print("Calibration complete.")
    print("Accel offsets: ax={} ay={} az={}".format(offset_ax, offset_ay, offset_az))
    print("Gyro offsets:  gx={} gy={} gz={}".format(offset_gx, offset_gy, offset_gz))
    return offset_ax, offset_ay, offset_az, offset_gx, offset_gy, offset_gz

# Calibrate before main loop
ax_off, ay_off, az_off, gx_off, gy_off, gz_off = calibrate()

while True:
    ax, ay, az, gx, gy, gz = read_accel_gyro()
    ax -= ax_off
    ay -= ay_off
    az -= az_off
    gx -= gx_off
    gy -= gy_off
    gz -= gz_off
    print('Accel: x={:6d} y={:6d} z={:6d} | Gyro: x={:6d} y={:6d} z={:6d}'.format(ax, ay, az, gx, gy, gz))
    time.sleep(0.5)
