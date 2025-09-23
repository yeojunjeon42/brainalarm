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
last_sw_state = GPIO.input(SW_PIN)

print("로터리 엔코더와 버튼 테스트를 시작합니다. Ctrl+C를 눌러 종료하세요.")

try:
    while True:
        # 로터리 엔코더 로직
        clk_state = GPIO.input(CLK_PIN)
        if clk_state != last_clk_state:  # CLK 핀에 변화가 있다면
            dt_state = GPIO.input(DT_PIN)
            if dt_state != clk_state:
                counter += 1
                print(f"시계 방향으로 회전 / 카운터: {counter}")
            else:
                counter -= 1
                print(f"반시계 방향으로 회전 / 카운터: {counter}")
        last_clk_state = clk_state

        # 버튼 로직
        sw_state = GPIO.input(SW_PIN)
        if sw_state != last_sw_state: # 버튼 상태에 변화가 있고
            if sw_state == 0: # 버튼이 눌렸다면 (FALLING)
                print("버튼이 눌렸습니다!")
        last_sw_state = sw_state
        
        # CPU 사용량을 줄이기 위해 약간의 딜레이를 줍니다.
        time.sleep(0.001)

except KeyboardInterrupt:
    print("\n테스트를 종료합니다.")
finally:
    GPIO.cleanup()