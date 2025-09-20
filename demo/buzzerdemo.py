import RPi.GPIO as GPIO
import time

BUZZER_PIN = 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

if __name__ == "__main__":
    try:
        while True:
            # For a passive buzzer, you can generate a tone by toggling the pin rapidly.
            # Example: play a 1kHz tone for 1 second
            frequency = 1000  # Hz
            duration = 1      # seconds
            period = 1.0 / frequency
            cycles = int(frequency * duration)
            for i in range(cycles):
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(period / 2)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                time.sleep(period / 2)
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Buzzer demo stopped")