import RPi.GPIO as GPIO
import time

# main.py에 설정된 핀 번호
CLK_PIN = 17
DT_PIN = 18

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    counter = 0
    clk_last_state = GPIO.input(CLK_PIN)

    print("엔코더 핀 상태 테스트. (Ctrl+C로 종료)")
    print("엔코더를 천천히 돌려보세요...")

    while True:
        clk_state = GPIO.input(CLK_PIN)
        dt_state = GPIO.input(DT_PIN)
        
        # 핀 상태를 항상 출력
        print(f"CLK: {clk_state} | DT: {dt_state}")

        if clk_state != clk_last_state:
            if dt_state != clk_state:
                counter += 1
            else:
                counter -= 1
            print(f"  └─ 회전! 카운터: {counter}")
        
        clk_last_state = clk_state
        time.sleep(0.05) # 출력이 너무 빠르지 않게 조절

except KeyboardInterrupt:
    print("\n테스트 종료.")
finally:
    GPIO.cleanup()