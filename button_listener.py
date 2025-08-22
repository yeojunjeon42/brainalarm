import RPi.GPIO as GPIO
import time
import subprocess

# 사용할 GPIO 핀 번호와 실행할 스크립트 경로 설정
BUTTON_PIN = 21
SCRIPT_PATH = '/brainalarm/program.py' # 사용자가 실행하려는 스크립트 경로

# 실행 중인 스크립트의 프로세스 객체를 저장할 변수
running_process = None

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

print("버튼 리스너 시작. 버튼을 눌러 스크립트를 제어하세요.")

try:
    while True:
        # 버튼이 눌렸을 때 (Rising Edge 감지)
        if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            
            # 1. 스크립트가 현재 실행 중인지 확인
            # running_process가 존재하고, .poll()의 결과가 None이면 아직 실행 중이라는 의미입니다.
            if running_process and running_process.poll() is None:
                # 실행 중이면, 프로세스를 종료합니다.
                print(f"버튼이 다시 눌렸습니다. '{SCRIPT_PATH}' 스크립트를 종료합니다.")
                running_process.terminate() # SIGTERM 신호를 보내 프로세스 종료
                running_process.wait() # 프로세스가 완전히 종료될 때까지 대기
                running_process = None # 변수 초기화
                print("스크립트가 종료되었습니다. 다시 버튼 입력을 기다립니다.")

            # 2. 스크립트가 실행 중이 아닐 때
            else:
                # 스크립트를 새로 실행합니다.
                print(f"버튼이 눌렸습니다. '{SCRIPT_PATH}' 스크립트를 실행합니다.")
                # Popen으로 스크립트를 실행하고, 그 프로세스 정보를 변수에 저장합니다.
                running_process = subprocess.Popen(['python', SCRIPT_PATH])
            
            # 디바운싱(Debouncing): 버튼이 한 번 눌렸을 때 여러 번 인식되는 것을 방지
            time.sleep(1)
            
        time.sleep(0.1) # CPU 사용량을 줄이기 위한 짧은 대기

except KeyboardInterrupt:
    print("프로그램을 종료합니다.")
    # 리스너 종료 시, 실행 중이던 스크립트가 있다면 함께 종료
    if running_process and running_process.poll() is None:
        running_process.terminate()
        running_process.wait()

finally:
    GPIO.cleanup() # GPIO 설정 초기화