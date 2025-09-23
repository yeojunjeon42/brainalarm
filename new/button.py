import RPi.GPIO as GPIO
import time

# 🚨 본인의 코드에 맞게 버튼이 연결된 GPIO 핀 번호로 수정하세요!
# 예: SET_BUTTON_PIN = 23, RESET_BUTTON_PIN = 4
BUTTON_PIN = 23  # 여기에 테스트하고 싶은 버튼의 핀 번호를 입력하세요.

try:
    GPIO.setmode(GPIO.BCM)
    # PUD_UP: 버튼을 누르지 않았을 때 HIGH(1), 눌렀을 때 LOW(0) 상태
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    print(f"[{BUTTON_PIN}번 핀] 버튼 테스트를 시작합니다. (Ctrl+C로 종료)")
    print("버튼을 눌렀다 떼보세요...")

    while True:
        # 핀의 현재 상태를 0.2초마다 읽어서 출력합니다.
        button_state = GPIO.input(BUTTON_PIN)
        
        # bình thường là 1, nút bấm là 0
        if button_state == 1:
            print("버튼 눌림 (상태: 0)")
        else:
            print("버튼 안 눌림 (상태: 1)")
            
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\n테스트 종료.")
finally:
    GPIO.cleanup()