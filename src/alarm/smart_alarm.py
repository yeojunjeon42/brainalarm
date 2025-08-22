import datetime
import time
from src.hardware.vibration_controller import trigger_vibration_alarm
# from src.processing.signal_processing import suBAR
from src.hardware.eeg import EEGReader
import sys
import os
import threading
from typing import Optional
from pytz import timezone
import RPi.GPIO as GPIO
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'hardware'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'display'))

#All time variables use UTC (python3)
TIMEGAP = 60*60*9

# 알람 작동
def trigger_alarm():
    """
    Trigger vibration alarm using the hardware vibration controller.
    Vibrates in 1-second on/off cycles until reset button is pressed.
    """
    trigger_vibration_alarm(vibrate_duration=1.0, pause_duration=0.2)

# wake window 내에 있는지 확인
#def  is_within_wake_window(datetime.datetime, datetime.time, int)
#wake_time은 current_time과 비교하여 알맞는 년, 월, 일, 시간, 분, 초에 설정되어야함
def is_within_wake_window(current_time, wake_time, window_min=15):
    current_time_timestamp = current_time.timestamp()
    wake_time_timestamp = wake_time.timestamp()
    if current_time_timestamp <= wake_time_timestamp and current_time_timestamp >= wake_time_timestamp + window_min*60:
        return True
    return False
    # current_minutes = current_time.hour * 60 + current_time.minute
    # wake_minutes = wake_time.hour * 60 + wake_time.minute
    # return abs(current_minutes - wake_minutes) <= window_min

# 대기 함수
# def wait_until_start(start_datetime : datetime.datetime, UTC+9로 입력됨)
def wait_until_start(start_datetime):
    UTC9_start_datetime = datetime.datetime.fromtimestamp(start_datetime.timestamp()+TIMEGAP)
    # 표기는 사용자 설정 시각인 UTC+9으로
    print(f"brainalarm 시작 예정 시각: {start_datetime.strftime('%H:%M:%S')}")
    print("현재시각:", end = ' ')
    print(datetime.datetime.now(timezone('Asia/Seoul')).strftime('%H:%M:%S'))
    while time.time() < start_datetime.timestamp() -TIMEGAP:
        time.sleep(30)

# 메인 함수
# smart_alarm_loop(
#     sleep_stage_model: object,            # scikit-learn 모델 같은 ML 모델 객체
#     start_time: datetime.datetime,        # 기상 탐색 시작 시각
#     wake_time: datetime.time,             # 목표 기상 시각
#     wake_window_min: int,                 # 기상 윈도우(분 단위)
#     args: argparse.Namespace              # CLI 인자 모음
# )
# def smart_alarm_loop(model, start_time, wake_time, wake_window_min, args):
#     alarm_triggered = False

#     # 1. 설정된 시간까지 대기
#     wait_until_start(start_time)
    
#     # Create EEG reader
#     eeg_reader = EEGReader(port=args.port, baudrate=args.baudrate)
#     if not eeg_reader.connect():
#         sys.exit(1)

#     # 2. smart alarm 작동
#     while not alarm_triggered:
#         now = datetime.datetime.now().time()

#         if is_within_wake_window(now, wake_time, wake_window_min):
#             if eeg_reader.feature is None:
#                 print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] EEG 데이터가 없습니다. 30초 후 다시 시도합니다.")
#                 predicted_stage = 0
#             #now 이전 30초의 EEG 데이터에서 scaled features 추출
#             else:
#                 predicted_stage = model.predict(eeg_reader.feature)

#             #N2면 1/ 아니면 0
#             if predicted_stage == 1:
#                 trigger_alarm()
#                 alarm_triggered = True
#         if now >= wake_time:
#             trigger_alarm()
#             alarm_triggered = True
#             eeg_reader.disconnect()
#             print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 기상 윈도우 종료됨.")
#             break

#         time.sleep(30)  # 30초 간격으로 체크
class SmartAlarm:
    def __init__(self, model, start_time, wake_time, wake_window_min, args):
        self.model = model
        self.start_time = start_time
        self.wake_time = wake_time
        self.wake_window_min = wake_window_min
        self.args = args

        # 1. EEGReader 객체는 미리 생성해두지만, 연결은 하지 않습니다.
        self.eeg_reader = EEGReader(port=self.args.port, baudrate=self.args.baudrate)
        self.thread: Optional[threading.Thread] = None
        self.running = False

    def start(self):
        """알람 루프 스레드를 시작합니다. EEG 리더는 아직 시작하지 않습니다."""
        if self.running:
            print("Alarm is already running.")
            return

        self.running = True
        # 2. _alarm_loop 스레드만 시작합니다.
        self.thread = threading.Thread(target=self._alarm_loop, daemon=True)
        self.thread.start()
        print("Smart alarm thread started. Waiting for wake window...")

    def stop(self):
        """알람 시스템과 실행 중인 모든 하위 스레드를 중지합니다."""
        if not self.running:
            return

        print("\nStopping smart alarm system...")
        self.running = False # 루프 중단 신호

        # 3. EEG 리더가 실행 중(running) 상태일 경우에만 중지 및 연결 해제를 시도합니다.
        if self.eeg_reader and self.eeg_reader.running:
            self.eeg_reader.stop()
            self.eeg_reader.disconnect()

        if self.thread and self.thread.is_alive():
            self.thread.join()
        
        print("Smart alarm system stopped.")

    def join(self):
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def _alarm_loop(self):
        """(스레드에서 실행됨) 스마트 알람 메인 로직."""
        wait_until_start(self.start_time)
        
        eeg_started = False # EEG 리더가 시작되었는지 확인하는 플래그

        while self.running:
            now_time = datetime.datetime.now().time()

            # 4. 기상 윈도우에 진입했는지 확인
            if is_within_wake_window(now_time, self.wake_time, self.wake_window_min):
                
                # 5. EEG 리더가 아직 시작되지 않았다면, 여기서 시작합니다.
                if not eeg_started:
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 기상 윈도우 진입. EEG 데이터 수집을 시작합니다.")
                    if self.eeg_reader.connect():
                        self.eeg_reader.start(mode='parsed')
                        eeg_started = True
                    else:
                        print("EEG 장치 연결 실패. 30초 후 재시도합니다.")
                        time.sleep(30)
                        continue # 연결 실패 시 다음 루프로 넘어감

                # 6. EEG 리더가 성공적으로 시작된 후에만 아래 로직을 수행합니다.
                if eeg_started:
                    feature = self.eeg_reader.feature
                    if feature is None:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] EEG 특징 데이터 수집 중... (30초 소요)")
                    else:
                        predicted_stage = self.model.predict(feature.reshape(1, -1))[0]
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 현재 수면 단계 예측: {predicted_stage}")

                        if predicted_stage == 1: # 얕은 수면으로 가정
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 얕은 수면 감지! 알람을 울립니다.")
                            trigger_alarm()
                            self.running = False # 알람 울렸으므로 종료
                            continue

            # 목표 기상 시간이 되면 무조건 알람 울림
            if now_time >= self.wake_time:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 목표 기상 시간 도달! 알람을 울립니다.")
                trigger_alarm()
                self.running = False # 알람 울렸으므로 종료
                continue
            
            # 30초 간격으로 체크
            time.sleep(30)
        
        print("Alarm loop finished.")
