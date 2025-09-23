import RPi.GPIO as GPIO
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import threading

#set up pins
BUZZER_PIN = 27
RESET_PIN = 4
SET_PIN = 23
VIBRATION_PIN = 27
CLK = 17
DT = 18

class PressType(Enum):
    """버튼 누름의 종류를 정의합니다."""
    NO_PRESS = 0
    SHORT_PRESS = 1
    LONG_PRESS = 2

# class Button:
#     def __init__(self, pin):
#         self.pin = pin
#         GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#         self.last_state = GPIO.input(self.pin) #default state is high
    
#     def was_pressed(self):
#         current_state = GPIO.input(self.pin)
#         was_pressed = (self.last_state == 1 and current_state == 0)
#         self.last_state = current_state
#         return was_pressed
class Button:
    """짧게 누르기와 길게 누르기를 감지하는 버튼 클래스"""
    def __init__(self, pin, long_press_duration=1.0):
        self.pin = pin
        self.long_press_duration = long_press_duration # 길게 누르기 시간 (기본값 1초)
        
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._last_state = GPIO.input(self.pin)
        self._press_start_time = 0
        self._long_press_triggered = False

    def get_event(self):
        """버튼의 상태를 확인하여 NO_PRESS, SHORT_PRESS, LONG_PRESS 이벤트를 반환합니다."""
        event = PressType.NO_PRESS
        current_state = GPIO.input(self.pin)

        # 버튼이 막 눌렸을 때 (Falling edge)
        if current_state == 0 and self._last_state == 1:
            self._press_start_time = time.time()
            self._long_press_triggered = False

        # 버튼이 계속 눌리고 있을 때
        elif current_state == 0 and self._last_state == 0:
            if not self._long_press_triggered:
                press_duration = time.time() - self._press_start_time
                if press_duration >= self.long_press_duration:
                    event = PressType.LONG_PRESS
                    self._long_press_triggered = True

        # 버튼에서 손을 뗐을 때 (Rising edge)
        elif current_state == 1 and self._last_state == 0:
            # 길게 누르기가 발동되지 않았을 경우에만 짧게 누르기로 간주
            if not self._long_press_triggered:
                event = PressType.SHORT_PRESS
            
            # 다음 입력을 위해 상태 초기화
            self._press_start_time = 0
            self._long_press_triggered = False

        self._last_state = current_state
        return event


class RotaryEncoder:
    """
    인터럽트 대신 폴링(Polling) 방식을 사용하여 로터리 엔코더의 입력을 감지하는 클래스.
    백그라운드 스레드를 사용하여 메인 프로그램의 동작을 방해하지 않습니다.
    """
    def __init__(self, clk_pin, dt_pin):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin

        # GPIO 핀 설정
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # 상태 저장을 위한 변수들
        self.change_value = 0
        self.clk_last_state = GPIO.input(self.clk_pin)
        self.lock = threading.Lock() # 스레드 간 데이터 충돌 방지를 위한 Lock
        self.running = True

        # 백그라운드에서 핀 상태를 계속 확인할 스레드 생성 및 시작
        # daemon=True로 설정하여 메인 프로그램 종료 시 스레드도 함께 종료되도록 함
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()

    def _poll_loop(self):
        """백그라운드 스레드에서 실행될 메인 루프"""
        while self.running:
            # 현재 CLK 핀 상태 읽기
            clk_state = GPIO.input(self.clk_pin)

            # CLK 핀의 상태가 이전과 다를 경우 (즉, 변화가 감지된 경우)
            if clk_state != self.clk_last_state:
                # DT 핀의 상태를 읽어서 회전 방향 판단
                dt_state = GPIO.input(self.dt_pin)
                
                # Lock을 사용하여 안전하게 self.change_value 수정
                with self.lock:
                    if dt_state != clk_state:
                        self.change_value += 1  # 시계 방향
                    else:
                        self.change_value -= 1  # 반시계 방향
            
            # 현재 CLK 상태를 마지막 상태로 저장
            self.clk_last_state = clk_state
            
            # CPU 사용량을 100%로 만들지 않기 위해 아주 잠깐 대기 (필수)
            time.sleep(0.001) # 1ms

    def get_change(self):
        """
        main.py에서 호출하는 함수.
        누적된 값(회전 정도)을 반환하고 0으로 초기화합니다.
        """
        with self.lock:
            value = self.change_value
            self.change_value = 0
        return value

    def stop(self):
        """백그라운드 스레드를 안전하게 종료하기 위한 함수"""
        self.running = False

class Buzzer:
    def __init__(self, pin, reset_pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        # reset_pin은 이제 Buzzer 클래스에서 직접 사용하지 않습니다.
        self.is_active = False

    def on(self):
        """버저를 켭니다."""
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        """버저를 끕니다."""
        GPIO.output(self.pin, GPIO.LOW)
    
    def stop(self):
        """알람 상태를 비활성화하고 버저를 끕니다."""
        self.is_active = False
        self.off()
        print("Buzzer stopped.")

class OLED:
    """
    OLED 스크린 제어를 담당하는 클래스.
    luma.oled 라이브러리의 복잡한 사용법을 간단한 메서드로 추상화합니다.
    """
    def __init__(self, port=1, address=0x3C):
        """
        OLED 객체를 초기화하고 스크린과의 연결을 설정합니다.
        - port: 라즈베리파이의 I2C 포트 번호 (보통 1)
        - address: OLED의 I2C 주소 (보통 0x3C)
        """

        try:
            # 1. I2C 통신 인터페이스를 설정합니다.
            self.serial = i2c(port=port, address=address)
            # 2. 통신 인터페이스를 사용하여 스크린 장치 드라이버를 설정합니다.
            self.device = ssd1306(self.serial)
            
            # 3. Pillow 라이브러리를 사용하여 폰트를 로드합니다.
            # (경로는 실제 폰트 파일 위치에 맞게 수정해야 합니다.)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            print("OLED 스크린이 성공적으로 초기화되었습니다.")
        except Exception as e:
            print(f"OLED 초기화 실패: {e}")
            self.device = None

    def _get_font(self, size):
        """요청된 크기에 맞는 폰트 객체를 반환하는 내부 헬퍼 함수입니다."""
        if size == 'large':
            return self.font_large
        return self.font_small

    def clear(self):
        """스크린을 깨끗하게 지웁니다."""
        if not self.device: return
        self.device.clear()

    def display(self, draw_function):
        """
        가장 핵심적인 그리기 함수입니다.
        'draw'라는 도화지 객체를 제공하고, 외부에서 받은 'draw_function'이
        이 도화지에 그림을 그리면, 최종 결과를 스크린에 표시합니다.
        """
        if not self.device: return
        with canvas(self.device) as draw:
            draw_function(draw, self) # draw 객체와 oled 객체 자신을 전달
