import RPi.GPIO as GPIO
GPIO.cleanup()
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
reset_pin = 4
GPIO.setup(reset_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
last_reset_state = GPIO.input(reset_pin)
while True:
    reset_state = GPIO.input(reset_pin)
    if last_reset_state == 1 and reset_state == 0:
        print("dd")
    last_reset_state = reset_state