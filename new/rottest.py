#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO
from hardware_handler import RotaryEncoder

# ===============================================================
# 사용자의 라즈베리파이 핀 연결에 맞게 이 부분을 수정하세요.
# ===============================================================
ENCODER_CLK_PIN = 17  # Encoder CLK 핀
ENCODER_DT_PIN = 18   # Encoder DT 핀
# ===============================================================

def main():
    """로터리 엔코더 테스트를 위한 메인 함수"""
    
    # GPIO 설정
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # RotaryEncoder 객체 생성
    # hardware_handler.py의 RotaryEncoder가 백그라운드 스레드를 바로 시작합니다.
    rotary_encoder = RotaryEncoder(ENCODER_CLK_PIN, ENCODER_DT_PIN)
    
    print("Rotary Encoder 테스트를 시작합니다.")
    print("엔코더를 돌리면 카운트가 변경됩니다.")
    print("종료하려면 Ctrl+C를 누르세요.")
    
    counter = 0 # 현재 카운트 값을 저장할 변수

    try:
        while True:
            # get_change()를 호출하여 마지막 확인 이후의 변화량을 가져옵니다.
            change = rotary_encoder.get_change()

            # 변화가 있었을 경우에만 카운트를 업데이트하고 출력합니다.
            if change != 0:
                counter += change
                direction = "시계 방향" if change > 0 else "반시계 방향"
                print(f"현재 카운트: {counter} (방향: {direction})")

            # 메인 루프가 CPU를 너무 많이 사용하지 않도록 잠시 대기합니다.
            time.sleep(0.05)

    except KeyboardInterrupt:
        # 사용자가 Ctrl+C를 누르면 실행됩니다.
        print("\n테스트를 종료합니다.")
        
    finally:
        # 프로그램이 어떤 이유로든 종료될 때 항상 실행됩니다.
        print("GPIO 설정을 초기화합니다.")
        rotary_encoder.stop() # 백그라운드 스레드 종료
        GPIO.cleanup()

if __name__ == "__main__":
    main()