# state_manager.py
from enum import Enum
from datetime import datetime, time, timedelta

class State(Enum):
    DISPLAY_TIME = 1
    SET_WAKE_WINDOW = 2
    SET_TARGET_TIME = 3

class StateManager:
    def __init__(self):
        self.current_state = State.DISPLAY_TIME
        self.wake_window = 30 # in minutes
        self.target_wake_time = time(7, 0)
        # ... 기타 설정 변수들

    def update(self, set_pressed, reset_pressed, encoder_change, sleep_stage):
        if reset_pressed:
            self._reset_all()
            return

        # 현재 상태에 따라 입력 처리
        if self.current_state == State.DISPLAY_TIME:
            if set_pressed:
                self.current_state = State.SET_WAKE_WINDOW
        
        elif self.current_state == State.SET_WAKE_WINDOW: # +5 minutes
            # 로터리 엔코더 값으로 wake_window 조절
            self.wake_window += encoder_change*5
            self.wake_window = min(max(self.wake_window, 5), 90) # 5~60분 사이로 제한
            if set_pressed:
                self.current_state = State.SET_TARGET_TIME

        elif self.current_state == State.SET_TARGET_TIME:
            # 로터리 엔코더 값으로 target_wake_time 조절
            total_minutes = self.target_wake_time.hour * 60 + self.target_wake_time.minute + encoder_change*5
            total_minutes = total_minutes % (24 * 60) # 24시간 형식
            self.target_wake_time = time(total_minutes // 60, total_minutes % 60)
            if set_pressed:
                self.current_state = State.DISPLAY_TIME

        # 알람 조건 확인 및 실행
        self._check_alarm_condition(sleep_stage)

    def _check_alarm_condition(self, sleep_stage):
        now = datetime.now().time()
        is_in_window = (self.target_wake_time - self.wake_window <= now < self.target_wake_time)
        is_target_time = (now >= self.target_wake_time)

        if (is_in_window and sleep_stage == "N2") or is_target_time:
            buzzer.start()
        
        # 알람 중지 조건 (예: 아무 버튼이나 누르면 중지)
        if (set_pressed or reset_pressed) and buzzer.is_active():
            buzzer.stop()

    def _reset_all(self):
        # 모든 설정 변수를 기본값으로 초기화
        self.current_state = State.DISPLAY_TIME
        # ...

    def render(self, oled):
        # 현재 상태에 맞는 UI를 OLED에 그림
        if self.current_state == State.DISPLAY_TIME:
            # 현재 시각, 설정된 알람 시간 등 표시
        elif self.current_state == State.SET_WAKE_WINDOW:
            # 기상 창 설정 UI 표시
        elif self.current_state == State.SET_TARGET_TIME