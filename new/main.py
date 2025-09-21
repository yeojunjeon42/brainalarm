# main.py
import time
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import os
import joblib
from state_manager import StateManager
from pytz import timezone

# --- 필요한 모듈 임포트 ---
# 각 파일에 실제 하드웨어 제어 클래스가 구현되어 있어야 합니다.
from hardware_handler import Buzzer, Button, RotaryEncoder, OLED
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
    BUZZER_PIN = 27
    SET_BUTTON_PIN = 23
    RESET_BUTTON_PIN = 4
    ENCODER_CLK_PIN = 17
    ENCODER_DT_PIN = 18

    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUZZER_PIN, GPIO.OUT)
    GPIO.setup(RESET_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) #pull up config
    GPIO.setup(SET_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(ENCODER_CLK_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
    GPIO.setup(ENCODER_DT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # 각 모듈의 객체를 생성합니다.
    buzzer = Buzzer(BUZZER_PIN)
    set_button = Button(SET_BUTTON_PIN)
    reset_button = Button(RESET_BUTTON_PIN)
    rotary_encoder = RotaryEncoder(ENCODER_CLK_PIN, ENCODER_DT_PIN)
    oled = OLED()
    
    # StateManager에 vibrator 객체를 전달하여 의존성을 주입합니다.
    state_manager = StateManager(buzzer)
    
    # EEG 분석기와 UI 렌더러 객체도 생성합니다.
    eeg_processor = EEGReader(sleep_stage_model, port='/dev/rfcomm0', baudrate=57600)
    renderer = UIRenderer()
    
    # 프로그램 시작 시 바로 스레드를 시작하지 않습니다.
    print("알람 시계 프로그램을 시작합니다. (Ctrl+C로 종료)")

    try:
        # =================================================================
        # 2. 메인 루프 (Main Loop)
        # =================================================================
        while True:
            # --- 2.1. 입력 감지 (Input Gathering) ---
            # 사용자의 버튼 및 엔코더 조작을 확인합니다.
            if set_button.was_pressed():
                state_manager.handle_set_press()

            if reset_button.was_pressed():
                state_manager.handle_reset_press()
            
            encoder_change = rotary_encoder.get_change()
            if encoder_change != 0:
                state_manager.handle_rotation(encoder_change)

            # --- 2.2. 뇌파 분석 스레드 관리 (EEG Thread Management) ---
            now_time = datetime.now(timezone('Asia/Seoul')).time()
            
            # StateManager로부터 현재 설정된 wake_window 시간을 계산합니다.
            target_dt = datetime.combine(datetime.today(timezone('Asia/Seoul')), state_manager.target_time)
            window_start_dt = target_dt - timedelta(minutes=state_manager.window_duration_minutes)
            window_start_time = window_start_dt.time()
            window_end_time = state_manager.target_time

            # 현재 시간이 wake_window 안에 있는지 확인합니다.
            is_in_window = window_start_time <= now_time < window_end_time
            eeg_is_running = eeg_processor.is_running()

            # --- 스레드 시작 조건 ---
            # 창 안에 있고, 알람이 울리지 않으며, 스레드가 꺼져 있을 때
            if is_in_window and not state_manager.alarm_active and not eeg_is_running:
                print(f"Wake window 시작({window_start_time.strftime('%H:%M')}). 뇌파 분석을 시작합니다.")
                eeg_processor.start_collection()

            # --- 스레드 중지 조건 ---
            # 창 밖에 있고, 스레드가 켜져 있을 때
            if not is_in_window and eeg_is_running:
                print(f"Wake window 종료. 뇌파 분석을 중지합니다.")
                eeg_processor.stop_collection()

            # --- 2.3. 상태 확인 및 로직 처리 (Logic Processing) ---
            # 스레드가 실행 중일 때만 뇌파를 확인하고 알람 조건을 체크합니다.
            if eeg_is_running and not state_manager.alarm_active:
                current_sleep_stage = eeg_processor.get_epoch_data(block=False)
                alarm_triggered = state_manager.check_alarm_condition(current_sleep_stage)
                
                if alarm_triggered:
                    print("알람 조건 충족! 진동을 시작합니다.")
                    # EEG 스레드는 이미 실행 중이므로, 중지하기만 하면 됩니다.
                    eeg_processor.stop_collection()
                    buzzer.start()
            
            # --- 2.4. 화면 출력 (Output Rendering) ---
            # 현재 상태에 맞는 화면을 그려달라고 Renderer에게 요청합니다.
            renderer.render(oled, state_manager)

            # --- 2.5. 처리 속도 조절 (Loop Delay) ---
            time.sleep(5)

    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    finally:
        # =================================================================
        # 3. 종료 단계 (Cleanup)
        # =================================================================
        # 프로그램이 어떤 이유로든 종료될 때 항상 실행됩니다.
        if eeg_processor.running(): # EEG 스레드가 여전히 실행 중이면 종료
            eeg_processor.stop_collection()
        eeg_processor.disconnect()
        buzzer.stop()
        GPIO.cleanup() # 모든 GPIO 설정을 깨끗하게 초기화합니다.

if __name__ == "__main__":
    main()