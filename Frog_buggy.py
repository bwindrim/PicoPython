from machine import Pin
from rp2 import bootsel_button
import time
from time import sleep
from dfplayermini import DFPlayerMini

led = Pin('LED', Pin.OUT)
hand = Pin(26, Pin. IN, Pin.PULL_UP)


# Define the GPIO pins for each stepper motor coil.
# Adapt these pin numbers to your Pico wiring.
MOTOR_PINS = {
    "front_left":  [8, 9, 10, 11],
    "front_right": [20, 21, 22, 7],
    "rear_left":   [12, 13, 14, 15],
    "rear_right":  [16, 17, 18, 19],
}

# 8-step unipolar sequence for smooth motion.
STEP_SEQUENCE = [
    (1, 0, 0, 0),
    (1, 1, 0, 0),
    (0, 1, 0, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 0),
    (0, 0, 1, 1),
    (0, 0, 0, 1),
    (1, 0, 0, 1),
]

class StepperMotor:
    def __init__(self, pins):
        self.pins = [Pin(pin, Pin.OUT) for pin in pins]
        self.step_index = 0
        self.release()

    def move(self, direction):
        self.step_index = (self.step_index + direction) % len(STEP_SEQUENCE)
        self._write_phase(STEP_SEQUENCE[self.step_index])

    def _write_phase(self, phase):
        for pin, value in zip(self.pins, phase):
            pin.value(value)

    def release(self):
        for pin in self.pins:
            pin.value(0)


class MecanumDrive:
    def __init__(self, motor_map):
        self.motors = {
            name: StepperMotor(pins)
            for name, pins in motor_map.items()
        }

    def set_velocity(self, vx, vy, omega, duration_ms, step_delay_ms=5):
        # vx: forward/backward (+ forward)
        # vy: right/left (+ right)
        # omega: rotation rate (+ CCW)
        speeds = {
            "front_left":  vx - vy - omega,
            "front_right": vx + vy + omega,
            "rear_left":   vx + vy - omega,
            "rear_right":  vx - vy + omega,
        }

        max_speed = max(abs(value) for value in speeds.values())
        if max_speed == 0:
            return

        # Normalize the speeds so the fastest motor steps once per loop.
        for key in speeds:
            speeds[key] /= max_speed

        accumulators = {name: 0.0 for name in self.motors}
        steps = duration_ms // step_delay_ms

        for _ in range(int(steps)):
            for name, speed in speeds.items():
                if speed == 0:
                    continue
                accumulators[name] += abs(speed)
                if accumulators[name] >= 1.0:
                    direction = 1 if speed > 0 else -1
                    self.motors[name].move(direction)
                    accumulators[name] -= 1.0
            time.sleep_ms(step_delay_ms)

    def stop(self):
        for motor in self.motors.values():
            motor.release()


def demo_sequence(buggy):
    print("Forward")
    buggy.set_velocity(vx=1, vy=0, omega=0, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Backward")
    buggy.set_velocity(vx=-1, vy=0, omega=0, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Right")
    buggy.set_velocity(vx=0, vy=1, omega=0, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Left")
    buggy.set_velocity(vx=0, vy=-1, omega=0, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Forward-right 45°")
    buggy.set_velocity(vx=1, vy=1, omega=0, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Forward-left 45°")
    buggy.set_velocity(vx=1, vy=-1, omega=0, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Backward-right 45°")
    buggy.set_velocity(vx=-1, vy=1, omega=0, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Backward-left 45°")
    buggy.set_velocity(vx=-1, vy=-1, omega=0, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Rotate anti-clockwise")
    buggy.set_velocity(vx=0, vy=0, omega=1, duration_ms=2000)
    buggy.stop()
    time.sleep_ms(500)

    print("Rotate clockwise")
    buggy.set_velocity(vx=0, vy=0, omega=-1, duration_ms=2000)
    buggy.stop()


if __name__ == "__main__":
    buggy = MecanumDrive(MOTOR_PINS)
    try:
        sleep(2)  # Allow time for the DFPlayer to initialize
        led.value(1)  # Turn on LED to indicate we're starting the test
        player1 = DFPlayerMini(1, 4, 5)
        print("DFPlayer Mini Test")
        result = player1.select_source('sdcard')
        print(f"Select Source Result: {result}")
        result = player1.query_num_files()
        print(f"Number of Files: {result}")
        result = player1.set_volume(25)
        print(f"Set Volume Result: {result}")

        while True:
            print("Press the BOOTSEL button to start the demo sequence...")
            led.value(1)  # Turn on LED to indicate we're starting the test
            while not bootsel_button() and hand.value():
                pass  # Wait for bootsel button press to start

            print("...starting demo sequence")
            result = player1.play(1)
            print(f"Play Result: {result}")
            sleep(5)
            demo_sequence(buggy)

    #        while not bootsel_button():
    #            pass  # Wait for bootsel button press to stop

            result = player1.stop()
            print(f"Stop Result: {result}")
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print("Error:", e)
    finally:
        buggy.stop()
        led.value(0)  # Turn off LED
        print("Motors released")
