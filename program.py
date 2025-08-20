import datetime
import time
import pandas as pd
import joblib
from src.display.oled_time_setter import settime, is_time_set, OLEDTimeSetter
from src.alarm.smart_alarm import smart_alarm_loop
import argparse
from src.hardware.eeg import EEGReader
import os


system = OLEDTimeSetter()
system.run()

# 사용자 설정
if is_time_set():
    h = (settime // 3600) % 24
    m = (settime // 60) % 60
    wake_time = datetime.time((h,m))  # 기상 목표 시각
    wake_window_min = 30  # 예정 시각 +-30분에서 N2 수면 단계 감지 시 알람 작동
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
    sleep_stage_model = joblib.load('final_model.joblib')



    # 실행
    smart_alarm_loop(sleep_stage_model, eeg_data, start_time, wake_time, wake_window_min, args)