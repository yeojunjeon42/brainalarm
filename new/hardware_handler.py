import RPi.GPIO as GPIO
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

#set up pins
BUZZER_PIN = 27
RESET_PIN = 4
SET_PIN = 23
VIBRATION_PIN = 27
CLK = 17
DT = 18

#GPIO setup
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(RESET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) #pull up config
GPIO.setup(SET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VIBRATION_PIN, GPIO.OUT)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class Button:
    def __init__(self, pin):
        self.pin = pin
        self.last_state = GPIO.input(self.pin) #default state is high
    
    def was_pressed(self):
        current_state = GPIO.input(self.pin)
        was_pressed = (self.last_state == 1 and current_state == 0)
        self.last_state = current_state
        return was_pressed

class RotaryEncoder:
    def __init__(self):
        self.last_clk = GPIO.input(CLK)
    
    def get_change(self):
        clk_state = GPIO.input(CLK)  # Read current CLK pin state
        if self.last_clk == 0 and clk_state == 1:  # Detect rising edge on CLK
            dt_state = GPIO.input(DT)  # Read DT pin state
            return (1 if dt_state == 0 else -1)  # Adjust by ±5
        self.last_clk = clk_state  # Store current state for next iteration

class Buzzer:
    def __init__(self):
        pass

    def start(self):
        try:
            while GPIO.input(RESET_PIN): #long press reset button to reset
                GPIO.output(BUZZER_PIN, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(BUZZER_PIN, GPIO.LOW)
                time.sleep(0.5)
        except KeyboardInterrupt:
            GPIO.output(BUZZER_PIN, GPIO.LOW)
            GPIO.cleanup()
    
    def stop(self):
        GPIO.output(BUZZER_PIN, GPIO.LOW)
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
        GPIO.cleanup()
        try:
            # 1. I2C 통신 인터페이스를 설정합니다.
            self.serial = i2c(port=port, address=address)
            # 2. 통신 인터페이스를 사용하여 스크린 장치 드라이버를 설정합니다.
            self.device = ssd1306(self.serial)
            
            # 3. Pillow 라이브러리를 사용하여 폰트를 로드합니다.
            # (경로는 실제 폰트 파일 위치에 맞게 수정해야 합니다.)
            self.font_small = ImageFont.truetype("fonts/D2Coding.ttf", 12)
            self.font_large = ImageFont.truetype("fonts/D2Coding.ttf", 24)
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

# Create instances to be imported
oled = OLED()
set_button = Button(SET_PIN)
reset_button = Button(RESET_PIN)
rotary_encoder = RotaryEncoder()
buzzer = Buzzer()