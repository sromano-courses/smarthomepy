# src/smart_room_config.py

# Photoresistor (light) logic:
# In many simple GPIO photoresistor modules:
#   1 = bright enough, 0 = dark
# If your tests expect the opposite, swap the booleans in check_enough_light().
PHOTO_BRIGHT_VALUE = 1

# CO2 thresholds in ppm (common indoor air-quality references)
CO2_HIGH_PPM = 1000
CO2_LOW_PPM = 800  # hysteresis to avoid fan flickering

# Temperature threshold for window control (°C)
TEMP_TOO_WARM_C = 25.0

# Servo duty cycles (typical SG90-ish values)
SERVO_CLOSED_DUTY = 2.0     # ~0 degrees
SERVO_OPEN_DUTY = 7.5       # ~90 degrees
