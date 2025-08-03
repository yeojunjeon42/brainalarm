import RPi.GPIO as GPIO
import time
GPIO.cleanup()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

reset_pin = 4
vibration_pin = 27
settime_pin = 23

GPIO.setup(reset_pin, GPIO.IN)
GPIO.setup(vibration_pin, GPIO.OUT)

CLK = 17
DT = 18

GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

counter = 0
last_clk = GPIO.input(CLK)
settime = time.time()
settime_fixed = False

def setting_time():
    global counter, last_clk, settime, settime_fixed
    try:
        while True:
            if not settime_fixed:
                clk_state = GPIO.input(CLK)
                dt_state = GPIO.input(DT)
                if clk_state != last_clk:
                    if dt_state != last_clk:
                        counter += 1
                    else:
                        counter -= 1
                    settime += counter * 60
                    last_clk = clk_state
                if GPIO.input(settime_pin) == GPIO.HIGH:
                    settime_fixed = True
                    counter = 0
            else:
                # settime이 고정된 상태에서 reset_pin을 체크
                if GPIO.input(reset_pin) == GPIO.HIGH:
                    settime = time.time()
                    settime_fixed = False
                    counter = 0
            time.sleep(0.001)
    except KeyboardInterrupt:
        GPIO.cleanup()