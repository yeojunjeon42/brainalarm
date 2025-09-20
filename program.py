import datetime
import time
import pandas as pd
import joblib
from src.display.oled_time_setter2 import OLEDTimeSetter
from src.alarm.smart_alarm import SmartAlarm
import argparse
import os
import sys
from src.hardware.vibration_controller import VibrationController
from pytz import timezone
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models/sleep_stage_classifier.joblib')


temp = datetime.datetime.now(timezone('Asia/Seoul'))
system = OLEDTimeSetter(temp)
system.run()

# 사용자 설정
if system.set_time_fixed:
    h_24 = system.set_hour
    m = system.set_minute
    is_pm = system.set_is_pm
    h_24 = h_24 % 24



    # ✅ 3. 변환된 24시간제 시간으로 datetime.time 객체 생성
    # 튜플이 아닌, 각 값을 인자로 전달합니다.
    now = datetime.datetime.now(timezone('Asia/Seoul'))
    wake_time_hm = datetime.time(h_24, m)
    wake_time = datetime.datetime.combine(datetime.datetime.now(timezone('Asia/Seoul')).date(), wake_time_hm)
    wake_time = timezone('Asia/Seoul').localize(wake_time)
    if wake_time < now:
        wake_time = wake_time + datetime.timedelta(days=1)
    wake_window_min = system.wake_window_minutes  # 예정 시각 -wake_window_min만큼에서 N2 수면 단계 감지 시 알람 작동
    start_time = wake_time - datetime.timedelta(minutes= wake_window_min)
    parser = argparse.ArgumentParser(description='EEG Data Reader for ThinkGear Protocol')
    parser.add_argument('--port', '-p', default='/dev/rfcomm0', 
                    help='Serial port (default: /dev/rfcomm0)')
    parser.add_argument('--baudrate', '-b', type=int, default=57600,
                    help='Baud rate (default: 57600)')
    parser.add_argument('--mode', '-m', choices=['hex', 'monitor'], default='hex',
                    help='Operation mode: hex (raw hex display) or monitor (parsed data)')
    
    args = parser.parse_args()
    

    # 모델 로드
    sleep_stage_model = joblib.load(MODEL_PATH)

    system2 = OLEDTimeSetter(wake_time)



    # 실행--> UTC + 9기준으로 입력됨
    alarm_system = SmartAlarm(sleep_stage_model, start_time, wake_time, wake_window_min, args, system2)


    try:
        alarm_system.start()
        alarm_system.join()
    except KeyboardInterrupt:
        print("\n사용자에 의해 프로그램이 중단되었습니다.")
    finally:
        alarm_system.stop()
        print("프로그램을 종료합니다.")