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

#GPIO setup
# GPIO.cleanup()
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(BUZZER_PIN, GPIO.OUT)
# GPIO.setup(RESET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) #pull up config
# GPIO.setup(SET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.setup(VIBRATION_PIN, GPIO.OUT)
# GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
# GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class Button:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.last_state = GPIO.input(self.pin) #default state is high
    
    def was_pressed(self):
        current_state = GPIO.input(self.pin)
        was_pressed = (self.last_state == 1 and current_state == 0)
        self.last_state = current_state
        return was_pressed

class RotaryEncoder:
    def __init__(self, clk_pin, dt_pin):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        
        # 스레드 충돌을 방지하기 위한 Lock 객체
        self.lock = threading.Lock()
        self.change_value = 0

        # GPIO 핀 설정
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # CLK 핀에 RISING(신호가 0->1이 될 때) 인터럽트 설정
        # 변화가 감지되면 self._callback 함수가 실행됩니다.
        GPIO.add_event_detect(self.clk_pin, GPIO.RISING, callback=self._callback, bouncetime=10)

    def _callback(self, channel):
        # 인터럽트 콜백 함수
        # DT 핀의 상태를 읽어 방향을 결정합니다.
        # 여러 신호가 동시에 접근하는 것을 막기 위해 lock을 사용합니다.
        with self.lock:
            dt_state = GPIO.input(self.dt_pin)
            if dt_state == 0:
                self.change_value += 1  # 정방향
            else:
                self.change_value -= 1  # 역방향

    def get_change(self):
        # main.py에서 호출하는 함수
        # 인터럽트를 통해 누적된 값을 반환하고 초기화합니다.
        with self.lock:
            value = self.change_value
            self.change_value = 0  # 값을 읽어간 후에는 0으로 리셋
        return value

class Buzzer:
    def __init__(self, pin, reset_pin):
        #GPIO setup
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        self.reset_pin = reset_pin

    def start(self):
        try:
            while GPIO.input(self.reset_pin): #long press reset button to reset
                GPIO.output(self.pin, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(self.pin, GPIO.LOW)
                time.sleep(0.5)
        except KeyboardInterrupt:
            GPIO.output(self.pin, GPIO.LOW)
            GPIO.cleanup()
    
    def stop(self):
        GPIO.output(self.pin, GPIO.LOW)
        GPIO.cleanup()

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
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
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
