# gpiozero_test.py
from gpiozero import Button
import time
import signal

# BCM 17번 핀으로 테스트
PIN = 17

def on_press():
    print(f"성공! >> {PIN}번 핀에서 입력 감지됨 (인터럽트 동작)")

try:
    # pull_up=True는 내부 저항을 사용하겠다는 의미입니다.
    button = Button(PIN, pull_up=True)
    button.when_pressed = on_press

    print(f"gpiozero 라이브러리 테스트 시작. {PIN}번 핀에 입력을 주세요...")
    print("(Ctrl+C로 종료)")

    # 스크립트가 바로 종료되지 않도록 대기
    signal.pause()

except Exception as e:
    print(f"오류 발생: {e}")