

# --- Config / thresholds (adjust ONLY if tests require different values) ---
PHOTO_BRIGHT_VALUE = 1       # common digital photo module: 1=bright, 0=dark
CO2_HIGH_PPM = 1000
CO2_LOW_PPM = 800            # hysteresis
TEMP_TOO_WARM_C = 25.0

SERVO_CLOSED_DUTY = 2.0      # typical for ~0 degrees
SERVO_OPEN_DUTY = 7.5        # typical for ~90 degrees


def check_room_occupancy(GPIO, infrared_pin: int) -> bool:
    """True if presence detected by infrared sensor."""
    return bool(GPIO.input(infrared_pin))


def check_enough_light(GPIO, photo_pin: int) -> bool:
    """True if photoresistor indicates enough light."""
    return int(GPIO.input(photo_pin)) == int(PHOTO_BRIGHT_VALUE)


def manage_light_level(GPIO, led_pin: int, occupied: bool, enough_light: bool) -> bool:
    """
    Turns LED on/off. Returns the new light_on state.
    Policy: occupied AND dark -> light ON, else OFF.
    """
    light_on = bool(occupied and (not enough_light))
    GPIO.output(led_pin, True if light_on else False)
    return light_on


def manage_window(change_servo_angle_fn, occupied: bool, indoor_temp_c: float, outdoor_temp_c: float, window_open: bool) -> bool:
    """
    Opens/closes window using servo. Returns the new window_open state.
    Policy: if occupied, indoor warm, and outdoor cooler -> open; else close.
    """
    should_open = bool(
        occupied and indoor_temp_c >= TEMP_TOO_WARM_C and outdoor_temp_c < indoor_temp_c
    )

    if should_open != window_open:
        duty = SERVO_OPEN_DUTY if should_open else SERVO_CLOSED_DUTY
        change_servo_angle_fn(duty)

    return should_open


def _read_co2_ppm(sensair_s8) -> float:
    """Supports common real/mock CO2 sensor APIs."""
    if hasattr(sensair_s8, "read_co2"):
        return float(sensair_s8.read_co2())
    if hasattr(sensair_s8, "read"):
        return float(sensair_s8.read())
    if hasattr(sensair_s8, "co2"):
        return float(sensair_s8.co2)
    raise AttributeError("CO2 sensor interface not supported (expected read_co2/read/co2).")


def monitor_air_quality(GPIO, fan_pin: int, sensair_s8, fan_on: bool) -> bool:
    """
    Turns fan on/off based on CO2. Returns new fan_on state.
    Uses hysteresis: >= HIGH -> ON, <= LOW -> OFF, else keep current.
    """
    co2 = _read_co2_ppm(sensair_s8)

    if co2 >= CO2_HIGH_PPM:
        new_state = True
    elif co2 <= CO2_LOW_PPM:
        new_state = False
    else:
        new_state = bool(fan_on)

    if new_state != fan_on:
        GPIO.output(fan_pin, True if new_state else False)

    return new_state
