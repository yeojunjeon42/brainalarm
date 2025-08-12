import datetime
import time
import pandas as pd
from xgboost.sklearn import XGBClassifier
from display.oled_time_setter import settime, is_time_set, OLEDTimeSetter
from src.alarm.smart_alarm import smart_alarm_loop
import os

# EEG 데이터 파일 경로 / eeg데이터가 동일한 디렉토리에 있어야 함
eeg_data = pd.read_csv('eeg_data.csv')

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

    # 모델 로드
    sleep_stage_model = XGBClassifier()
    model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'xgb_model.json')
    sleep_stage_model.load_model(model_path)



    # 실행
    smart_alarm_loop(sleep_stage_model, eeg_data, start_time, wake_time, wake_window_min)