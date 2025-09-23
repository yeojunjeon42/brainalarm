import RPi.GPIO as GPIO
import time

# GPIO 핀 번호 설정 (BCM 모드)
CLK_PIN = 17
DT_PIN = 18
SW_PIN = 23

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 변수 초기화
counter = 0
last_clk_state = GPIO.input(CLK_PIN)

# --- 디바운싱을 위한 변수 추가 ---
last_press_time = 0  # 마지막으로 버튼이 눌린 시간을 저장
DEBOUNCE_DELAY = 0.2 # 0.2초의 딜레이 설정

print("로터리 엔코더와 버튼 테스트를 시작합니다. (디바운싱 적용)")
print("Ctrl+C를 눌러 종료하세요.")

try:
    while True:
        # 1. 로터리 엔코더 로직
        clk_state = GPIO.input(CLK_PIN)
        if clk_state != last_clk_state:
            dt_state = GPIO.input(DT_PIN)
            if dt_state != clk_state:
                counter += 1
                print(f"시계 방향으로 회전 / 카운터: {counter}")
            else:
                counter -= 1
                print(f"반시계 방향으로 회전 / 카운터: {counter}")
            # 엔코더 자체의 미세한 떨림을 막기 위한 약간의 딜레이
            time.sleep(0.002)
        last_clk_state = clk_state

        # 2. 버튼 로직 (디바운싱 적용)
        sw_state = GPIO.input(SW_PIN)
        
        # 버튼이 눌렸고(sw_state == 0), 마지막으로 눌린 후 0.2초가 지났다면
        if sw_state == 1 and (time.time() - last_press_time) > DEBOUNCE_DELAY:
            print("버튼이 눌렸습니다!")
            last_press_time = time.time() # 마지막으로 눌린 시간을 현재 시간으로 업데이트

        # 전체 루프의 CPU 사용량을 줄이기 위한 최소한의 딜레이
        time.sleep(0.001)

except KeyboardInterrupt:
    print("\n테스트를 종료합니다.")
finally:
    GPIO.cleanup()