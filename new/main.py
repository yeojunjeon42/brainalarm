# main.py
from state_manager import StateManager
from hardware_handler import oled, set_button, reset_button, rotary_encoder, vibrator
from eeg_handler import EEGProcessor
import time

# 1. 하드웨어 및 EEG 처리기 초기화
eeg_processor = EEGProcessor()
eeg_processor.start() # 뇌파 분석 스레드 시작

state_manager = StateManager()

try:
    while True:
        # 2. 입력 감지
        set_pressed = set_button.was_pressed()
        reset_pressed = reset_button.was_pressed()
        encoder_change = rotary_encoder.get_change()
        
        # 3. 현재 수면 단계 가져오기
        current_sleep_stage = eeg_processor.get_current_stage()

        # 4. 상태 업데이트 및 로직 처리
        state_manager.update(set_pressed, reset_pressed, encoder_change, current_sleep_stage)

        # 5. 현재 상태에 맞는 화면 그리기
        state_manager.render(oled)

        time.sleep(0.05) # CPU 사용량 조절

finally:
    eeg_processor.stop()
    vibrator.stop()
    print("프로그램 종료")