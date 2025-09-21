import RPi.GPIO as GPIO
import time

# 사용할 GPIO 핀 번호 설정 (BCM 모드)
INTERRUPT_PIN = 26

# GPIO 핀 번호 체계를 BCM으로 설정
GPIO.setmode(GPIO.BCM)

# 26번 핀을 입력으로 설정하고, 내부 풀다운 저항을 활성화합니다.
# 버튼을 누르지 않았을 때 LOW 상태(0V)를 유지하고, 눌렀을 때 HIGH 상태(3.3V)가 됩니다.
# 만약 풀업 저항을 사용하려면 GPIO.PUD_UP으로 설정하고 회로 연결을 변경해야 합니다.
GPIO.setup(INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# 인터럽트 발생 시 실행될 콜백 함수 정의
def interrupt_callback(channel):
    """
    이 함수는 인터럽트가 감지될 때마다 호출됩니다.
    """
    print(f"✅ 인터럽트 발생! (핀 번호: {channel})")
    # 여기에 인터럽트 발생 시 수행할 작업을 추가할 수 있습니다.
    # 예: LED 켜기, 데이터 전송 등

print("인터럽트 대기 중... (Ctrl+C를 눌러 종료)")

try:
    # 인터럽트 설정
    # GPIO.add_event_detect(핀 번호, 감지할 신호, callback=콜백 함수, bouncetime=중복 방지 시간(ms))
    # GPIO.RISING: 신호가 LOW에서 HIGH로 변경될 때 (버튼 누를 때)
    # GPIO.FALLING: 신호가 HIGH에서 LOW로 변경될 때 (버튼 뗄 때)
    # GPIO.BOTH: RISING과 FALLING 모두 감지
    GPIO.add_event_detect(INTERRUPT_PIN, GPIO.RISING, callback=interrupt_callback, bouncetime=200)

    # 프로그램이 바로 종료되지 않도록 무한 루프 실행
    while True:
        # print("...메인 프로그램 실행 중...") # 주석 해제 시 메인 스레드가 동작하는 것을 확인 가능
        time.sleep(1)

except KeyboardInterrupt:
    print("\n프로그램 종료. GPIO 정리 중...")
finally:
    # 프로그램 종료 시 GPIO 설정 초기화
    GPIO.cleanup()