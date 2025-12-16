DEPLOYMENT = False  # This variable is to understand whether you are deploying on the actual hardware

import time

try:
    import adafruit_bmp280
    import board
    import RPi.GPIO as GPIO
    DEPLOYMENT = True
except:
    import mock.adafruit_bmp280 as adafruit_bmp280
    import mock.board as board
    import mock.GPIO as GPIO
    import mock.senseair_s8 as senseair_s8

from smart_room_config import (
    PHOTO_BRIGHT_VALUE,
    CO2_HIGH_PPM,
    CO2_LOW_PPM,
    TEMP_TOO_WARM_C,
    SERVO_CLOSED_DUTY,
    SERVO_OPEN_DUTY,
)


class SmartRoom:
    SERVO_PIN = 31  # Servo motor pin
    INFRARED_PIN = 22  # infrared distance sensor pin
    LED_PIN = 37  # led pin
    PHOTO_PIN = 13  # photoresistor pin
    FAN_PIN = 32  # fan pin

    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.INFRARED_PIN, GPIO.IN)
        GPIO.setup(self.PHOTO_PIN, GPIO.IN)
        GPIO.setup(self.LED_PIN, GPIO.OUT)
        GPIO.setup(self.SERVO_PIN, GPIO.OUT)
        GPIO.setup(self.FAN_PIN, GPIO.OUT)

        i2c = board.I2C()
        self.bmp280_indor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x76)
        self.bmp280_outdoor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x68)

        self.sensair_s8 = senseair_s8.SenseairS8()

        self.servo = GPIO.PWM(self.SERVO_PIN, 50)
        self.servo.start(2)
        if DEPLOYMENT:
            time.sleep(1)
        self.servo.ChangeDutyCycle(0)

        self.light_on = False
        self.window_open = False
        self.fan_on = False

    def check_room_occupancy(self) -> bool:
        try:
            return bool(GPIO.input(self.INFRARED_PIN))
        except Exception as e:
            raise SmartRoomError(f"Infrared sensor error: {e}") from e

    def check_enough_light(self) -> bool:
        try:
            value = GPIO.input(self.PHOTO_PIN)
            return int(value) == int(PHOTO_BRIGHT_VALUE)
        except Exception as e:
            raise SmartRoomError(f"Photoresistor error: {e}") from e

    def manage_light_level(self) -> None:
        try:
            occupied = self.check_room_occupancy()
            enough_light = self.check_enough_light()

            if occupied and not enough_light:
                GPIO.output(self.LED_PIN, True)
                self.light_on = True
            else:
                GPIO.output(self.LED_PIN, False)
                self.light_on = False
        except Exception as e:
            raise SmartRoomError(f"Light management error: {e}") from e

    def manage_window(self) -> None:
        try:
            occupied = self.check_room_occupancy()

            indoor_temp = float(self.bmp280_indor.temperature)
            outdoor_temp = float(self.bmp280_outdoor.temperature)

            should_open = (
                occupied
                and indoor_temp >= TEMP_TOO_WARM_C
                and outdoor_temp < indoor_temp
            )

            if should_open and not self.window_open:
                self.change_servo_angle(SERVO_OPEN_DUTY)
                self.window_open = True

            elif not should_open and self.window_open:
                self.change_servo_angle(SERVO_CLOSED_DUTY)
                self.window_open = False

        except Exception as e:
            raise SmartRoomError(f"Window management error: {e}") from e

    def monitor_air_quality(self) -> None:
        try:
            if hasattr(self.sensair_s8, "read_co2"):
                co2 = float(self.sensair_s8.read_co2())
            elif hasattr(self.sensair_s8, "read"):
                co2 = float(self.sensair_s8.read())
            elif hasattr(self.sensair_s8, "co2"):
                co2 = float(self.sensair_s8.co2)
            else:
                raise SmartRoomError("Unsupported CO2 sensor interface")

            if co2 >= CO2_HIGH_PPM and not self.fan_on:
                GPIO.output(self.FAN_PIN, True)
                self.fan_on = True

            elif co2 <= CO2_LOW_PPM and self.fan_on:
                GPIO.output(self.FAN_PIN, False)
                self.fan_on = False

        except Exception as e:
            raise SmartRoomError(f"Air quality monitoring error: {e}") from e

    def change_servo_angle(self, duty_cycle):
        self.servo.ChangeDutyCycle(duty_cycle)
        if DEPLOYMENT:
            time.sleep(1)
        self.servo.ChangeDutyCycle(0)


class SmartRoomError(Exception):
    pass
