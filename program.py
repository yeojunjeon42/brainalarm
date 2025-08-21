import datetime
import time
import pandas as pd
import joblib
from src.display.oled_time_setter import OLEDTimeSetter
from src.alarm.smart_alarm import smart_alarm_loop
import argparse
from src.hardware.eeg import EEGReader
import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models/final_model.joblib')


system = OLEDTimeSetter()
system.run()

# 사용자 설정
if system.set_time_fixed:
    h_12 = system.set_hour
    m = system.set_minute
    is_pm = system.set_is_pm
    # 2. 24시간제로 변환
    h_24 = h_12
    if is_pm and h_12 != 12:
        h_24 += 12
    elif not is_pm and h_12 == 12:
        h_24 = 0
    h_24 = h_24 % 24

    # ✅ 3. 변환된 24시간제 시간으로 datetime.time 객체 생성
    # 튜플이 아닌, 각 값을 인자로 전달합니다.
    wake_time = datetime.time(h_24, m)  # 기상 목표 시각
    wake_window_min = system.wake_window  # 예정 시각 +-30분에서 N2 수면 단계 감지 시 알람 작동
    start_time = (datetime.datetime.combine(datetime.date.today(), wake_time)
              - datetime.timedelta(minutes=wake_window_min)) # 탐색 시작 시각
    
    parser = argparse.ArgumentParser(description='EEG Data Reader for ThinkGear Protocol')
    parser.add_argument('--port', '-p', default='/dev/serial0', 
                       help='Serial port (default: /dev/serial0)')
    parser.add_argument('--baudrate', '-b', type=int, default=57600,
                       help='Baud rate (default: 57600)')
    parser.add_argument('--mode', '-m', choices=['hex', 'monitor'], default='hex',
                       help='Operation mode: hex (raw hex display) or monitor (parsed data)')
    
    args = parser.parse_args()
    
    # Create EEG reader
    eeg_reader = EEGReader(port=args.port, baudrate=args.baudrate)

    # 모델 로드
    sleep_stage_model = joblib.load(MODEL_PATH)



    # 실행
    smart_alarm_loop(sleep_stage_model, start_time, wake_time, wake_window_min, args)