# main.py
from state_manager import StateManager
from hardware_handler import oled, set_button, reset_button, rotary_encoder, buzzer
from eeg_handler import EEGReader
import time
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import os
import joblib
from state_manager import StateManager

# --- 필요한 모듈 임포트 ---
# 각 파일에 실제 하드웨어 제어 클래스가 구현되어 있어야 합니다.
from hardware_handler import Vibrator, Button, RotaryEncoder, OLED
from eeg_handler import EEGReader
from ui_renderer import UIRenderer
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'models/sleep_stage_classifier.joblib')
sleep_stage_model = joblib.load(MODEL_PATH)

def main():
    """메인 실행 함수"""
    # =================================================================
    # 1. 초기화 단계 (Initialization)
    # =================================================================
    # GPIO 핀 번호를 실제 연결에 맞게 정의합니다.
    VIBRATOR_PIN = 27
    SET_BUTTON_PIN = 23
    RESET_BUTTON_PIN = 4
    ENCODER_CLK_PIN = 17
    ENCODER_DT_PIN = 18

    # 각 모듈의 객체를 생성합니다.
    vibrator = Vibrator(VIBRATOR_PIN)
    set_button = Button(SET_BUTTON_PIN)
    reset_button = Button(RESET_BUTTON_PIN)
    rotary_encoder = RotaryEncoder(ENCODER_CLK_PIN, ENCODER_DT_PIN)
    oled = OLED()
    
    # StateManager에 vibrator 객체를 전달하여 의존성을 주입합니다.
    state_manager = StateManager(vibrator)
    
    # EEG 분석기와 UI 렌더러 객체도 생성합니다.
    eeg_processor = EEGReader(sleep_stage_model, port='/rfcomm0', baudrate=57600)
    renderer = UIRenderer()
    
    # 프로그램 시작 시 바로 스레드를 시작하지 않습니다.
    print("알람 시계 프로그램을 시작합니다. (Ctrl+C로 종료)")

try:
    while True:
        # 2. 입력 감지
        set_pressed = set_button.was_pressed()
        reset_pressed = reset_button.was_pressed()
        encoder_change = rotary_encoder.get_change()
        
        # 3. 현재 수면 단계 가져오기
        current_sleep_stage = eeg_processor.get_epoch_data(block=False) # 1이 N2 stage

        # 4. 상태 업데이트 및 로직 처리
        state_manager.update(set_pressed, reset_pressed, encoder_change, current_sleep_stage)

        # 5. 현재 상태에 맞는 화면 그리기
        state_manager.render(oled)

        time.sleep(0.05) # CPU 사용량 조절

finally:
    eeg_processor.stop()
    buzzer.stop()
    print("프로그램 종료")