import RPi.GPIO as GPIO
import time

# 문제가 발생하는 17번 핀을 테스트합니다.
PIN = 23

def my_callback(channel):
    print(f"성공! >> 인터럽트 감지됨: {channel}번 핀")

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    print(f"{PIN}번 핀에 인터럽트 설정을 시도합니다...")
    GPIO.add_event_detect(PIN, GPIO.RISING, callback=my_callback, bouncetime=200)
    print("인터럽트 설정 성공. 입력을 기다립니다. (Ctrl+C로 종료)")
    
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("프로그램 종료.")
except Exception as e:
    print(f"오류 발생: {e}")
finally:
    print("GPIO 정리.")
    GPIO.cleanup()