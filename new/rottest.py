#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# ===============================================================
# 사용자의 라즈베리파이 핀 연결에 맞게 이 부분을 수정하세요.
# ===============================================================
ENCODER_CLK_PIN = 17  # Encoder CLK 핀 (A pin)
ENCODER_DT_PIN = 18   # Encoder DT 핀 (B pin)
SET_BUTTON_PIN = 23   # SET 버튼 핀 (SW pin)
# ===============================================================

def main():
    """
    RPi.GPIO 라이브러리만 사용하여 로터리 엔코더와 버튼 입력을
    직접 처리하는 테스트 스크립트.
    """
    # GPIO 설정
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # 핀 모드 설정: 엔코더와 버튼 모두 입력(IN)으로 설정하고,
    # 내부 풀업 저항을 활성화하여 안정적인 신호를 받습니다.
    GPIO.setup(ENCODER_CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCODER_DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SET_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # 상태 저장을 위한 변수 초기화
    counter = 0
    # 엔코더 CLK 핀의 이전 상태를 저장. 시작 시 현재 상태로 초기화.
    clk_last_state = GPIO.input(ENCODER_CLK_PIN)
    # 버튼의 이전 상태를 저장. 버튼은 눌리지 않았을 때 HIGH(1) 상태.
    button_last_state = GPIO.input(SET_BUTTON_PIN)

    print("RAW 하드웨어 테스트를 시작합니다.")
    print("엔코더를 돌리거나 SET 버튼을 눌러보세요.")
    print("종료하려면 Ctrl+C를 누르세요.")

    try:
        while True:
            # --- 1. 로터리 엔코더 로직 ---
            clk_state = GPIO.input(ENCODER_CLK_PIN)
            dt_state = GPIO.input(ENCODER_DT_PIN)
            
            # CLK 핀의 상태가 이전과 달라졌을 때 (즉, 한 칸 움직였을 때)
            if clk_state != clk_last_state:
                # DT 핀의 상태를 확인하여 방향을 판단
                if dt_state != clk_state:
                    # CLK와 DT의 상태가 다르면 시계 방향
                    counter += 1
                    print(f"엔코더: 시계 방향 / 현재 값: {counter}")
                else:
                    # CLK와 DT의 상태가 같으면 반시계 방향
                    counter -= 1
                    print(f"엔코더: 반시계 방향 / 현재 값: {counter}")
            
            # 현재 CLK 상태를 다음 루프를 위해 저장
            clk_last_state = clk_state

            # --- 2. 버튼 로직 (간단한 디바운싱 포함) ---
            button_state = GPIO.input(SET_BUTTON_PIN)
            
            # 버튼 상태가 이전과 다를 때
            if button_state != button_last_state:
                # 버튼이 눌렸을 때 (HIGH(1) -> LOW(0))만 감지
                if button_state == 0:
                    print(">> SET 버튼이 눌렸습니다! <<")
                # 0.05초의 딜레이를 주어 버튼이 떨리는 '바운싱' 현상을 방지
                time.sleep(0.05)
            
            # 현재 버튼 상태를 다음 루프를 위해 저장
            button_last_state = button_state
            
            # CPU 사용량을 줄이기 위한 약간의 딜레이
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n테스트를 종료합니다.")
    finally:
        print("GPIO 설정을 초기화합니다.")
        GPIO.cleanup()

if __name__ == "__main__":
    main()