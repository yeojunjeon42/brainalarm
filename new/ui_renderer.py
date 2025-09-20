# ui_renderer.py
from datetime import datetime
from state_manager import State # State Enum 임포트

class UIRenderer:
    def __init__(self):
        # UI에 필요한 리소스(예: 아이콘 이미지)가 있다면 여기서 로드합니다.
        pass

    def render(self, oled, state_manager):
        """
        StateManager의 현재 상태를 기반으로 적절한 화면을 OLED에 렌더링합니다.
        """
        # oled.display() 메서드에 실제 그리는 함수를 전달합니다.
        oled.display(lambda draw: self._draw_scene(draw, state_manager))

    def _draw_scene(self, draw, state_manager):
        """
        어떤 화면을 그릴지 결정하고 해당 그리기 함수를 호출하는 라우터 역할.
        'draw'는 luma.oled의 canvas 객체입니다.
        """
        # 1순위: 알람이 활성화되었는지 먼저 확인
        if state_manager.alarm_active:
            self._draw_alarm_screen(draw, state_manager)
            return

        # 2순위: 현재 상태에 따라 다른 화면 호출
        state = state_manager.current_state
        if state == State.DISPLAY_TIME:
            self._draw_display_time_screen(draw, state_manager)
        elif state == State.SET_WINDOW_DURATION:
            self._draw_set_duration_screen(draw, state_manager)
        elif state == State.SET_TARGET_TIME:
            self._draw_set_target_time_screen(draw, state_manager)

    def _draw_alarm_screen(self, draw, state_manager):
        now_str = datetime.now().strftime('%H:%M:%S')
        draw.text((15, 10), "WAKE UP!", font=oled._get_font('large'), fill="white")
        draw.text((40, 40), now_str, font=oled._get_font('small'), fill="white")

    def _draw_display_time_screen(self, draw, state_manager):
        now_str = datetime.now().strftime('%H:%M:%S')
        target_str = state_manager.target_time.strftime('%H:%M')
        duration = state_manager.window_duration_minutes

        draw.text((25, 10), now_str, font=oled._get_font('large'), fill="white")
        draw.text((20, 40), f"Alarm: {target_str} ({duration}min)", font=oled._get_font('small'), fill="white")

    def _draw_set_duration_screen(self, draw, state_manager):
        duration = state_manager.temp_window_duration_minutes
        draw.text((10, 10), "Set Window", font=oled._get_font('small'), fill="white")
        draw.text((25, 30), f"< {duration:02d} min >", font=oled._get_font('large'), fill="white")

    def _draw_set_target_time_screen(self, draw, state_manager):
        temp_time = state_manager.temp_target_time
        hour_str = f"{temp_time.hour:02d}"
        minute_str = f"{temp_time.minute:02d}"

        # 편집 모드에 따라 텍스트 주변에 상자(강조)를 그립니다.
        if state_manager.edit_mode.name == 'HOUR':
            draw.rectangle((30, 28, 58, 48), outline="white", fill="black")
        else: # MINUTE
            draw.rectangle((68, 28, 96, 48), outline="white", fill="black")

        draw.text((10, 10), "Set Target Time", font=oled._get_font('small'), fill="white")
        draw.text((32, 30), f"{hour_str}:{minute_str}", font=oled._get_font('large'), fill="white")