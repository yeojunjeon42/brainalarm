import RPi.GPIO as GPIO
import time

# 테스트할 GPIO 핀 번호
READ_PIN = 23

GPIO.setmode(GPIO.BCM)
# 풀다운 저항으로 설정. 버튼을 누르면 1, 안 누르면 0이 됩니다.
GPIO.setup(READ_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print(f"GPIO {READ_PIN}번 핀 읽기 테스트. (Ctrl+C로 종료)")

try:
    while True:
        pin_state = GPIO.input(READ_PIN)
        print(f"핀 상태: {pin_state}")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\n테스트 종료.")
finally:
    GPIO.cleanup()