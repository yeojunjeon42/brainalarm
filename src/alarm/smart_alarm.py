import datetime
import time
from sklearn.preprocessing import StandardScaler
from processing.feature_extract import exfeature
from hardware.vibration_controller import trigger_vibration_alarm
from SuBAR import suBAR
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'processing'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'hardware'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'display'))



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
    while datetime.datetime.now() < (start_datetime):
        time.sleep(30)

# 메인 함수
def smart_alarm_loop(model,eegdata, start_time, wake_time, wake_window_min):
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
            if deltime < 30:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 아직 EEG 데이터가 충분하지 않습니다. 현재 시간: {now}, 시작 시간: {begin_time.time()}")
                break
            parsed_eeg_data = eegdata.iloc[deltime-30:deltime]  # 최근 30초의 EEG 데이터
            features = get_feature_scaled(parsed_eeg_data)
            predicted_stage = model.predict(features)[0]
            #N2면 1/ 아니면 0
            if predicted_stage == 1:
                trigger_alarm()
                alarm_triggered = True
        else:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 기상 윈도우 종료됨.")
            break

        time.sleep(30)  # 30초 간격으로 체크
