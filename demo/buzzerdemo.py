import RPi.GPIO as GPIO
import time

BUZZER_PIN = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

if __name__ == "__main__":
    try:
        while True:
            GPIO.output(BUZZER_PIN, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(BUZZER_PIN, GPIO.LOW)
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Buzzer demo stopped")