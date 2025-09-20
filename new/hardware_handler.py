import RPi.GPIO as GPIO
import time

#set up pins
BUZZER_PIN = 27,RESET_PIN = 4,SET_PIN = 23,VIBRATION_PIN = 27,CLK = 17,DT = 18

#GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(RESET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) #pull up config
GPIO.setup(SET_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(VIBRATION_PIN, GPIO.OUT)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

class OLED:
    def __init__(self):
        pass
    
    # Methods will be called by state_manager.render()
    # Add other display methods as needed

class Button(self,pin):
    def __init__(self):
        self.pin = pin
        self.last_state = GPIO.input(self.pin) #default state is high
    
    def was_pressed(self):
        current_state = GPIO.input(self.pin)
        was_pressed = (self.last_state == 1 and current_state == 0)
        self.last_state = current_state
        return was_pressed

class RotaryEncoder:
    def __init__(self):
        self.last_clk = GPIO.input(self.CLK)
    
    def get_change(self):
        clk_state = GPIO.input(self.CLK)  # Read current CLK pin state
        if self.last_clk == 0 and clk_state == 1:  # Detect rising edge on CLK
            dt_state = GPIO.input(self.DT)  # Read DT pin state
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

# Create instances to be imported
oled = OLED()
set_button = Button(SET_PIN)
reset_button = Button(RESET_PIN)
rotary_encoder = RotaryEncoder()
buzzer = Buzzer()