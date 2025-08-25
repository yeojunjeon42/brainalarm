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
# def is_within_wake_window(current_time, wake_time, window_min=15):
#     current_time_timestamp = current_time.timestamp()
#     wake_time_timestamp = wake_time.timestamp()
#     if current_time_timestamp <= wake_time_timestamp and current_time_timestamp >= wake_time_timestamp + window_min*60:
#         return True
#     return False
def is_within_wake_window(current_time, wake_time, window_min=15):
    print('running')
    current_time_timestamp = current_time.timestamp()
    print(current_time_timestamp)
    alarm_time = datetime.datetime.combine(datetime.date.today(), wake_time)
    if alarm_time<current_time : 
      alarm_time = alarm_time + datetime.timedelta(days = 1)
      print('alarm_time_adjusted')
    print(alarm_time)
    wake_time_timestamp = alarm_time.timestamp()
    print(wake_time_timestamp)
    if current_time_timestamp <= wake_time_timestamp and current_time_timestamp >= wake_time_timestamp + window_min*60:
        return True
    return False




# 대기 함수
# def wait_until_start(start_datetime : datetime.datetime, UTC+9로 입력됨)
def wait_until_start(start_datetime):
    UTC9_start_datetime = datetime.datetime.fromtimestamp(start_datetime.timestamp()+TIMEGAP)
    # 표기는 사용자 설정 시각인 UTC+9으로
    print(f"brainalarm 시작 예정 시각: {start_datetime.strftime('%H:%M:%S')}")
    print("현재시각:", end = ' ')
    print(start_datetime)
    print(datetime.datetime.now())
    print(datetime.datetime.now(timezone('Asia/Seoul')).strftime('%H:%M:%S'))
    while time.time() < start_datetime.timestamp() -TIMEGAP:
        print('waiting until start time...', end='\r')
        time.sleep(5)

class SmartAlarm:
    def __init__(self, model, start_time, wake_time, wake_window_min, args, oled_system):
        self.model = model
        self.start_time = start_time
        self.wake_time = wake_time
        self.wake_window_min = wake_window_min
        self.args = args
        self.oled_system = oled_system

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
        print('alarm loop started')
        eeg_started = False # EEG 리더가 시작되었는지 확인하는 플래그

        while self.running:
            loop_start_time = time.monotonic()
            now_time = datetime.datetime.now() #지금 한국 시간으로 바꿔야 함-> 처리는 UTC, 출력만 UTC+9
                

            # 4. 기상 윈도우에 진입했는지 확인
            if is_within_wake_window(now_time, self.wake_time, self.wake_window_min):
                self.oled_system.running = False # OLED 시간 설정 모드 종료
                # 5. EEG 리더가 아직 시작되지 않았다면, 여기서 시작합니다.
                if not eeg_started:
                    #출력은 한국 시간
                    print(f"[{datetime.datetime.now(timezone('Asia/Seoul')).strftime('%H:%M:%S')}] 기상 윈도우 진입. EEG 데이터 수집을 시작합니다.")
                    if self.eeg_reader.connect():
                        self.eeg_reader.start(mode='parsed')
                        eeg_started = True
                    else:
                        print("EEG 장치 연결 실패. 30초 후 재시도합니다.")
                        time.sleep(30)
                        continue # 연결 실패 시 다음 루프로 넘어감

                # 6. EEG 리더가 성공적으로 시작된 후에만 아래 로직을 수행합니다.
                if eeg_started:
                    if self.eeg_reader.new_feature_ready:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}]New EEG feature available for prediction.")
                        if self.eeg_reader.signal_quality > self.eeg_reader.noise_threshold:
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 신호 품질이 좋지 않습니다 ({self.eeg_reader.signal_quality}%). 다시 시도합니다.")
                        else:
                            feature_vector = self.eeg_reader.feature
                            feature = feature_vector.reshape(1, -1)
                            predicted_stage = self.model.predict(feature)[0]
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 현재 수면 단계 예측: {predicted_stage}")

                            if predicted_stage == 1: # 얕은 수면으로 가정
                                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 얕은 수면 감지! 알람을 울립니다.")
                                trigger_alarm()
                                self.running = False # 알람 울렸으므로 종료
                        self.eeg_reader.new_feature_ready = False
                    else:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 새로운 EEG 특징이 아직 준비되지 않았습니다. 기다립니다...")

            # 목표 기상 시간이 되면 무조건 알람 울림
            if now_time >= self.wake_time:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 목표 기상 시간 도달! 알람을 울립니다.")
                trigger_alarm()
                self.running = False # 알람 울렸으므로 종료

            elapsed_time = time.monotonic() - loop_start_time
            sleep_duration = 30 - elapsed_time
            if sleep_duration > 0:
                time.sleep(sleep_duration)
        
        print("Alarm loop finished.")
