import datetime
import time
import pandas as pd
import numpy as np
from xgboost.sklearn import XGBClassifier
from sklearn.preprocessing import StandardScaler
from feature_extract import exfeature
from settingtime import settime, settime_fixed, setting_time
from SuBAR import suBAR

# EEG 데이터 파일 경로 / eeg데이터가 동일한 디렉토리에 있어야 함
eeg_data = pd.read_csv('eeg_data.csv')

scaler = StandardScaler()


# EEG 데이터 수집 및 전처리 함수(parsed_eeg_data는 칼럼 이름이 'fp1', 'fp2'만 존재)
def get_feature_scaled(parsed_eeg_data):
    # 진폭이 50 이상인 지점 존재하면 suBAR 돌리기
    if (parsed_eeg_data['fp1'].abs() > 50).any() or (parsed_eeg_data['fp2'].abs() > 50).any():
        parsed_eeg_data = suBAR(parsed_eeg_data)
    features = exfeature(parsed_eeg_data)  # 특징 추출 함수
    return scaler.fit_transform(features)

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
    #알람 돌아가기 시작한 시간
    begin_time = datetime.datetime.now()

    # 1. 설정된 시간까지 대기
    wait_until_start(start_time)

    # 2. smart alarm 작동
    while not alarm_triggered:
        now = datetime.datetime.now().time()

        if is_within_wake_window(now, wake_time, wake_window_min):
            #now 이전 30초의 EEG 데이터에서 scaled features 추출
            deltime = int((now - begin_time.time()).total_seconds())
            parsed_eeg_data = eeg_data.iloc[deltime:deltime+30]  # 최근 30초의 EEG 데이터
            features = get_feature_scaled(parsed_eeg_data)
            predicted_stage = sleep_stage_model.predict(features)[0]
            #N2면 1/ 아니면 0
            if predicted_stage == 1:
                trigger_alarm()
                alarm_triggered = True
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 기상 윈도우 종료됨.")
            break

        time.sleep(30)  # 30초 간격으로 체크

setting_time()

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