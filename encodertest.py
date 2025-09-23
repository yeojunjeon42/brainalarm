import RPi.GPIO as GPIO
import time

# 사용하고 있는 핀 번호를 입력하세요
CLK_PIN = 17
DT_PIN = 18

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 이전 상태를 저장할 변수
last_clk_state = GPIO.input(CLK_PIN)
last_dt_state = GPIO.input(DT_PIN)

print("Encoder test started. Press Ctrl+C to exit.")
print("CLK | DT")
print("----|----")

try:
    while True:
        # 현재 상태 읽기
        clk_state = GPIO.input(CLK_PIN)
        dt_state = GPIO.input(DT_PIN)

        # 상태가 변경되었을 때만 출력
        if clk_state != last_clk_state or dt_state != last_dt_state:
            print(f" {clk_state}  |  {dt_state}")

        # 현재 상태를 이전 상태로 저장
        last_clk_state = clk_state
        last_dt_state = dt_state

        time.sleep(0.001) # CPU 부담을 줄이기 위한 아주 짧은 딜레이

except KeyboardInterrupt:
    print("\nTest finished.")
finally:
    GPIO.cleanup()