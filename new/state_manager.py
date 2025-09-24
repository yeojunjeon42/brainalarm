# state_manager.py
from enum import Enum, auto
from datetime import datetime, time, timedelta, timezone

kst = timezone(timedelta(hours=9))

class State(Enum):
    """시계의 현재 상태를 나타냅니다."""
    DISPLAY_TIME = auto()
    SET_WINDOW_DURATION = auto()
    SET_TARGET_TIME = auto()

class EditMode(Enum):
    """시간 설정 시 '시' 또는 '분'을 편집 중인지 나타냅니다."""
    HOUR = auto()
    MINUTE = auto()

class StateManager:
    """시계의 상태와 로직을 총괄하는 클래스"""
    def __init__(self, Buzzer):
        """
        StateManager를 초기화합니다.
        - vibrator: 진동 모터 제어 객체를 외부에서 주입받습니다.
        """
        self.buzzer = Buzzer
        self._reset()

    def _reset(self):
        """모든 상태와 설정값을 기본값으로 초기화합니다."""
        self.current_state = State.DISPLAY_TIME
        self.edit_mode = EditMode.HOUR

        # 최종 저장될 설정값
        self.window_duration_minutes = 30  # 기상 창 크기 (기본값: 30분)
        #self.target_time = time(7, 0)      # 최종 기상 시간 (기본값: 오전 7시)
        self.target_time = datetime.combine(datetime.now(kst).date(),time(7,0))+timedelta(days = 1) #기본값: 다음날 오전 7시
        self.target_time = self.target_time.replace(tzinfo=kst)
        # 사용자가 편집 중인 값을 임시로 저장하는 변수
        self.temp_window_duration_minutes = self.window_duration_minutes
        self.temp_target_time = self.target_time
        
        # 알람이 활성화되었는지 나타내는 플래그
        self.alarm_active = False
        print("모든 설정이 초기화되었습니다.")

    def handle_set_press(self):
        """'Set' 버튼 입력을 처리하여 상태를 전환합니다."""
        # 알람이 울리는 중에는 설정 모드로 진입하지 않습니다.
        if self.alarm_active:
            return

        if self.current_state == State.DISPLAY_TIME:
            self.current_state = State.SET_WINDOW_DURATION
            return

        if self.current_state == State.SET_WINDOW_DURATION:
            self.window_duration_minutes = self.temp_window_duration_minutes
            self.current_state = State.SET_TARGET_TIME
            self.edit_mode = EditMode.HOUR
            return

        if self.current_state == State.SET_TARGET_TIME:
            if self.edit_mode == EditMode.HOUR:
                self.edit_mode = EditMode.MINUTE
            else: # '분' 편집 모드였을 경우
                # self.target_time = self.temp_target_time
                self.target_time = datetime.combine(datetime.now(kst).date(),self.temp_target_time).replace(tzinfo=kst)
                if datetime.now(kst).time() >= self.temp_target_time : 
                    #현재 시각보다 늦다면 다음날 알람 설정
                    self.target_time =self.target_time + timedelta(days = 1)
                self.current_state = State.DISPLAY_TIME
                self.edit_mode = EditMode.HOUR

    def handle_reset_press(self):
        """'Reset' 버튼 입력을 처리합니다."""
        # 알람이 울리는 중에 눌렸다면, 먼저 알람을 끕니다.
        if self.alarm_active:
            self.stop_alarm()
        
        # 모든 설정을 초기화합니다.
        self._reset()

    def handle_rotation(self, change):
        """로터리 엔코더 입력을 처리하여 임시 설정값을 조절합니다."""
        if self.current_state == State.SET_WINDOW_DURATION:
            self.temp_window_duration_minutes += change
            # 값이 비정상적으로 커지거나 작아지는 것을 방지
            if self.temp_window_duration_minutes < 5: self.temp_window_duration_minutes = 5
            if self.temp_window_duration_minutes > 90: self.temp_window_duration_minutes = 90

        elif self.current_state == State.SET_TARGET_TIME:
            self.temp_target_time = self._adjust_time(self.temp_target_time, change)

    def _adjust_time(self, time_obj, change):
        """편집 모드(시/분)에 따라 시간을 조절하는 헬퍼 함수입니다."""
        if isinstance(time_obj, datetime):
            current_time = time_obj.time()
        else:
            current_time = time_obj
        dt = datetime.combine(datetime.now(kst).date(), current_time)
        delta = timedelta(hours=change) if self.edit_mode == EditMode.HOUR else timedelta(minutes=change)
        return (dt + delta).time()

    def check_alarm_condition(self, sleep_stage):
        """
        알람 조건을 확인합니다. 조건 충족 시 True를 반환하여
        main.py에 EEG 해제와 진동 시작을 알립니다.
        """
        if self.alarm_active:
            return False

        now = datetime.now(kst)
        now_time = now.time()

        target_datetime = self.target_time
        window_start_datetime = target_datetime - timedelta(minutes=self.window_duration_minutes)
        # calculated_window_start_time = window_start_datetime.time()

        is_in_window = window_start_datetime <= now < self.target_time
        is_target_time = now >= self.target_time

        # 조건 충족 시, 알람을 활성화하고 True를 반환하여 main.py에 알립니다.
        if is_target_time or (is_in_window and sleep_stage == 1): #N2면 1
            self.alarm_active = True
            return True
            
        return False

    def stop_alarm(self):
        """알람을 중지하고 관련 상태를 리셋합니다."""
        self.buzzer.stop()
        self.alarm_active = False
        print("알람 중지됨.")