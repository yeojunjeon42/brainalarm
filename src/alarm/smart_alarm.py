import datetime
import time
from xgboost.sklearn import XGBClassifier
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'hardware'))

from feature_extract import exfeature
from gpio_time_setter import settime, settime_fixed


# EEG 데이터 수집 및 전처리 함수
def get_latest_sleep_data():
    raw_data = ...  # 센서에서 데이터 수집
    features = exfeature(raw_data)  # 특징 추출 함수
    return features

# 알람 작동
def trigger_alarm():
    print("알람")
    # 실제 알람 구현: 사운드, LED 등 추가 가능

# wake window 내에 있는지 확인
def is_within_wake_window(current_time, wake_time, window_min=15):
    current_minutes = current_time.hour * 60 + current_time.minute
    wake_minutes = wake_time.hour * 60 + wake_time.minute
    return abs(current_minutes - wake_minutes) <= window_min

# 대기 함수
def wait_until_start(start_datetime):
    print(f"brainalarm 시작 예정 시각: {start_datetime.strftime('%H:%M:%S')}")
    while datetime.datetime.now() < (start_datetime):
        time.sleep(30)

# 메인 함수
def smart_alarm_loop():
    alarm_triggered = False

    # 1. 설정된 시간까지 대기
    wait_until_start(start_time)

    # 2. smart alarm 작동

    while not alarm_triggered:
        now = datetime.datetime.now().time()

        if is_within_wake_window(now, wake_time, wake_window_min):
            features = get_latest_sleep_data()
            predicted_stage = sleep_stage_model.predict([features])[0]

            if predicted_stage == 'N2':
                trigger_alarm()
                alarm_triggered = True
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 기상 윈도우 종료됨.")
            break

        time.sleep(30)  # 30초 간격으로 체크


# 사용자 설정
if settime_fixed:
    h = (settime // 3600) % 24
    m = (settime // 60) % 60
    wake_time = datetime.time((h,m))  # 기상 목표 시각
    wake_window_min = 30  # 예정 시각 +-30분에서 N2 수면 단계 감지 시 알람 작동
    start_time = (datetime.datetime.combine(datetime.date.today(), wake_time)
              - datetime.timedelta(minutes=wake_window_min)) # 탐색 시작 시각

    # 모델 로드
    sleep_stage_model = XGBClassifier()
    sleep_stage_model.load_model('xgb_model.json')



    # 실행
    smart_alarm_loop()