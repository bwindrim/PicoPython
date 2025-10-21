from machine import Pin, PWM, I2C
from time import ticks_ms, ticks_diff, sleep_ms
import math

# === MPU6050 Setup ===
#from mpu6050 import MPU6050  # use a simple MicroPython mpu6050.py driver
from mpu6050 import MPU6050
i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
imu = MPU6050(i2c)

# === Motor Setup ===
# Motor A
A1 = PWM(Pin(0))
A2 = PWM(Pin(1))

# Motor B
B1 = PWM(Pin(14))
B2 = PWM(Pin(15))

# Configure PWM frequency
A1.freq(1000)   # 1 kHz - not silent
A2.freq(1000)   # Set frequency for A2
B1.freq(1000)
B2.freq(1000)   # Set frequency for B2

MAX_SPEED = 60000  # Max duty cycle for 16-bit PWM

def motor_a(speed):
    """Speed from -1.0 to +1.0"""
    assert -1.0 <= speed <= 1.0, "Speed must be between -1.0 and +1.0"
    #print("Motor A speed:", speed)
#    return
    if speed == 0:
        A1.duty_u16(0)
        A2.duty_u16(0)
    elif speed > 0:
        A1.duty_u16(int(MAX_SPEED * speed))
        A2.duty_u16(0)
    else:
        A1.duty_u16(0)
        A2.duty_u16(int(MAX_SPEED * -speed))  # reverse full

def motor_b(speed):
    """Speed from -1.0 to +1.0"""
    assert -1.0 <= speed <= 1.0, "Speed must be between -1.0 and +1.0"
    #print("Motor B speed:", speed)
#    return
    if speed == 0:
        B1.duty_u16(0)
        B2.duty_u16(0)
    elif speed > 0:
        B1.duty_u16(int(MAX_SPEED * speed))
        B2.duty_u16(0)
    else:
        B1.duty_u16(0)
        B2.duty_u16(int(MAX_SPEED * -speed))


# === Complementary filter variables ===
angle = 0.0  # initial angle
alpha = 0.98    # gyro weight
dt = 0.005      # 5 ms loop interval

# === PID gains ===
Kp = 0.5
Kd = 0.1
Ki = 0.0
integral = 0.0
prev_error = 0.0

# === Loop timing ===
last = ticks_ms()

try:
    imu.calibrate()  # calibrate gyro
    print("Starting balance loop in three seconds...")
    sleep_ms(3000)
    print("...starting now!")
    iter_count = 0
    start = ticks_ms()
    while True:
        now = ticks_ms()
        if ticks_diff(now, last) < 5:
            continue  # maintain 200 Hz
        last = now
        iter_count += 1

        # ---- 1. Read IMU ----
        acc = imu.get_accel()
        gyro = imu.get_gyro()

        # Calculate pitch from accelerometer
#        print("Accel data: x={:.2f} y={:.2f} z={:.2f}".format(acc['x'], acc['y'], acc['z']))
        acc_angle = math.degrees(math.atan2(-acc['x'], acc['z']))
        acc_angle += -88.0  # adjust for mounting angle
#        print("Acc angle: {:.2f} deg".format(acc_angle))

        # Integrate gyro rate to angle
        gyro_rate = gyro['y']  # deg/s
#        print("Gyro rate: {:.2f} deg/s".format(gyro_rate))
        angle = alpha * (angle + gyro_rate * dt) + (1 - alpha) * acc_angle
#        print("Angle: {:.2f} deg".format(angle))

        # ---- 2. PID control ----
        error = 0.0 - angle  # target upright = 0 deg
        integral += error * dt
        derivative = (error - prev_error) / dt
        output = Kp * error + Ki * integral + Kd * derivative
        prev_error = error
#        print("PID output: {:.2f}".format(output), "E={:.2f} I={:.2f} D={:.2f}".format(Kp*error, Ki*integral, Kd*derivative))

        # Limit output to [-1, 1]
        output = max(min(output, 1.0), -1.0)
#        print("PID output: {:.2f}".format(output))

        # ---- 3. Drive motors ----
        if abs(acc_angle) < 45.0:  # only drive if not too tilted
            motor_a(-output)
            motor_b(-output)
        else:
            motor_a(0)
            motor_b(0)
#            print("Too tilted! Motors off.")

        # ---- 4. Small delay ----
        # (loop already ~5 ms, so minimal sleep)
except KeyboardInterrupt:
    motor_a(0)
    motor_b(0)
    print("Done, motors off.")
    run_time_ms = ticks_diff(ticks_ms(), start)
    print("Total run time: {} mS".format(run_time_ms))
    print("Total iterations: {}".format(iter_count))
    print("Rate = {} mS per iteration.".format(run_time_ms / iter_count))

