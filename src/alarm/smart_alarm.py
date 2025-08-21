import datetime
import time
from src.hardware.vibration_controller import trigger_vibration_alarm
# from src.processing.signal_processing import suBAR
from src.hardware.eeg import EEGReader
import argparse
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'hardware'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'display'))



# 알람 작동
def trigger_alarm():
    """
    Trigger vibration alarm using the hardware vibration controller.
    Vibrates in 1-second on/off cycles until reset button is pressed.
    """
    trigger_vibration_alarm(vibrate_duration=1.0, pause_duration=0.2)

# wake window 내에 있는지 확인
def is_within_wake_window(current_time, wake_time, window_min=15):
    current_minutes = current_time.hour * 60 + current_time.minute
    wake_minutes = wake_time.hour * 60 + wake_time.minute
    return abs(current_minutes - wake_minutes) <= window_min

# 대기 함수
def wait_until_start(start_datetime):
    print(f"brainalarm 시작 예정 시각: {start_datetime.strftime('%H:%M:%S')}")
    print(datetime.datetime.now().strftime('%H:%M:%S'))
    while datetime.datetime.now() < (start_datetime):
        time.sleep(30)

# 메인 함수
def smart_alarm_loop(model, start_time, wake_time, wake_window_min, args):
    alarm_triggered = False

    # 1. 설정된 시간까지 대기
    wait_until_start(start_time)
    
    # Create EEG reader
    eeg_reader = EEGReader(port=args.port, baudrate=args.baudrate)
    if not eeg_reader.connect():
        sys.exit(1)

    # 2. smart alarm 작동
    while not alarm_triggered:
        now = datetime.datetime.now().time()

        if is_within_wake_window(now, wake_time, wake_window_min):
            if eeg_reader.feature is None:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] EEG 데이터가 없습니다. 30초 후 다시 시도합니다.")
            #now 이전 30초의 EEG 데이터에서 scaled features 추출
            else:
                predicted_stage = model.predict(eeg_reader.feature)

            #N2면 1/ 아니면 0
            if predicted_stage == 1:
                trigger_alarm()
                alarm_triggered = True
        if now >= wake_time:
            trigger_alarm()
            alarm_triggered = True
            eeg_reader.disconnect()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 기상 윈도우 종료됨.")
            break

        time.sleep(30)  # 30초 간격으로 체크
