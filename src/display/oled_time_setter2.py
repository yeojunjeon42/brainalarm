#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLED Time Setter System (Refactored)
- All state variables are encapsulated within the OLEDTimeSetter class.
- Global variables have been removed for better code structure and reusability.
"""

import time
import threading
import datetime
import RPi.GPIO as GPIO
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from pytz import timezone

TIMEGAP = 60*60*9 # UTC+9 (Seoul)

class OLEDTimeSetter:
    def __init__(self):
        # GPIO Setup
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Pin definitions
        self.reset_pin = 4
        self.set_pin = 23
        self.vibration_pin = 27
        self.CLK = 17
        self.DT = 18
        
        # Setup GPIO pins
        GPIO.setup(self.reset_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.set_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.vibration_pin, GPIO.OUT)
        GPIO.setup(self.CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Rotary encoder state
        self.last_clk = GPIO.input(self.CLK)
        
        # --- State Management (Encapsulated Instance Variables) ---
        # No more global variables. All state is managed within the instance.
        self.wake_window_minutes = 30  # Default wake window
        self.wake_window_fixed = False # Has the window been confirmed?

        self.set_hour = 12
        self.set_minute = 0
        self.set_is_pm = True
        self.set_time_fixed = False  # Has the time been confirmed?
        self.settime = time.time()   # Unix timestamp for the set wake time
        
        # Interface state management
        self.interface_mode = 'WINDOW'  # WINDOW, TIME, CLOCK
        self.time_is_blinking = True
        self.last_blink_time = time.time()
        self.blink_state = True
        
        # Button state tracking
        self.last_reset_state = GPIO.input(self.reset_pin)
        self.last_set_state = GPIO.input(self.set_pin)
        
        # OLED Setup
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c)
        self.image = Image.new("1", (128, 64))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts
        try:
            self.time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            self.ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            self.window_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        except IOError:
            self.time_font = ImageFont.load_default()
            self.ampm_font = ImageFont.load_default()
            self.window_font = ImageFont.load_default()
        
        # System state
        self.running = True
        
        print("OLED Time Setter initialized (Refactored)")
        print("Interface: Wake window selection -> Time setting -> Clock")

    # --- Convenience functions are now methods of the class ---
    def get_set_time_info(self):
        """
        Get the current set time information. Now a method of the class.
        """
        if self.set_time_fixed:
            set_dt = datetime.datetime.fromtimestamp(self.settime)
            return {
                'settime': self.settime,
                'settime_fixed': self.set_time_fixed,
                'hour': set_dt.hour,
                'minute': set_dt.minute,
                'formatted': set_dt.strftime('%I:%M %p'),
                'wake_window_minutes': self.wake_window_minutes,
                'wake_window_fixed': self.wake_window_fixed
            }
        else:
            return {
                'settime': self.settime,
                'settime_fixed': False,
                'hour': None,
                'minute': None,
                'formatted': 'Not Set',
                'wake_window_minutes': self.wake_window_minutes if self.wake_window_fixed else None,
                'wake_window_fixed': self.wake_window_fixed
            }

    def is_time_set(self):
        """Check if wake time has been set and confirmed."""
        return self.set_time_fixed
        
    def is_wake_window_set(self):
        """Check if wake window has been set"""
        return self.wake_window_fixed

    def update_display(self):
        """Update OLED display based on current interface mode"""
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        
        if self.interface_mode == 'WINDOW':
            self.draw_window_interface()
        elif self.interface_mode == 'TIME':
            self.draw_time_interface()
        elif self.interface_mode == 'CLOCK':
            self.draw_clock_interface()
        
        self.oled.image(self.image)
        self.oled.show()
    
    def draw_window_interface(self):
        """Draw the wake window selection interface"""
        title = "Wake Window"
        title_bbox = self.draw.textbbox((0, 0), title, font=self.ampm_font)
        title_x = (128 - (title_bbox[2] - title_bbox[0])) // 2
        self.draw.text((title_x, 5), title, font=self.ampm_font, fill=255)
        
        window_text = f"{self.wake_window_minutes} mins"
        window_bbox = self.draw.textbbox((0, 0), window_text, font=self.window_font)
        window_x = (128 - (window_bbox[2] - window_bbox[0])) // 2
        self.draw.text((window_x, 25), window_text, font=self.window_font, fill=255)
    
    def draw_time_interface(self):
        """Draw the time setting interface with blinking"""
        current_time = time.time()
        if self.blink_state:
            if current_time - self.last_blink_time >= 1.9:
                self.blink_state = False
                self.last_blink_time = current_time
        else:
            if current_time - self.last_blink_time >= 0.1:
                self.blink_state = True
                self.last_blink_time = current_time
        
        if not self.time_is_blinking or self.blink_state:
            display_hour = self.set_hour
            if display_hour == 0: display_hour = 12
            elif display_hour > 12: display_hour -= 12
        
            time_text = f"{display_hour:02d}:{self.set_minute:02d}"
            ampm_text = "PM" if self.set_is_pm else "AM"
            
            bbox = self.draw.textbbox((0, 0), time_text, font=self.time_font)
            time_x = (128 - (bbox[2] - bbox[0])) // 2
            self.draw.text((time_x, 18), time_text, font=self.time_font, fill=255)
            
            ampm_bbox = self.draw.textbbox((0, 0), ampm_text, font=self.ampm_font)
            ampm_x = (128 - (ampm_bbox[2] - ampm_bbox[0])) // 2
            self.draw.text((ampm_x, 43), ampm_text, font=self.ampm_font, fill=255)
        
        window_info = f"{self.wake_window_minutes}min before"
        window_bbox = self.draw.textbbox((0, 0), window_info, font=self.ampm_font)
        window_x = (128 - (window_bbox[2] - window_bbox[0])) // 2
        self.draw.text((window_x, 54), window_info, font=self.ampm_font, fill=255)
    
    def draw_clock_interface(self):
        """Draw the clock interface showing current time and alarm time"""
        now = datetime.datetime.now(timezone('Asia/Seoul'))  # KST
        current_hour = now.hour
        
        display_current_hour = current_hour
        if display_current_hour == 0: display_current_hour = 12
        elif display_current_hour > 12: display_current_hour -= 12
        
        current_ampm = "PM" if current_hour >= 12 else "AM"
        current_time_text = f"{display_current_hour:02d}:{now.minute:02d}"
        
        bbox = self.draw.textbbox((0, 0), current_time_text, font=self.time_font)
        time_x = (128 - (bbox[2] - bbox[0])) // 2
        self.draw.text((time_x, 18), current_time_text, font=self.time_font, fill=255)
        
        ampm_bbox = self.draw.textbbox((0, 0), current_ampm, font=self.ampm_font)
        ampm_x = (128 - (ampm_bbox[2] - ampm_bbox[0])) // 2
        self.draw.text((ampm_x, 43), current_ampm, font=self.ampm_font, fill=255)
        
        if self.set_time_fixed:

            alarm_dt = datetime.datetime.fromtimestamp(self.settime + TIMEGAP)
            alarm_hour = alarm_dt.hour
            
            display_alarm_hour = alarm_hour
            if display_alarm_hour == 0: display_alarm_hour = 12
            elif display_alarm_hour > 12: display_alarm_hour -= 12

            alarm_text = f"{display_alarm_hour:02d}:{alarm_dt.minute:02d}"
            alarm_bbox = self.draw.textbbox((0, 0), alarm_text, font=self.ampm_font)
            alarm_x = 128 - (alarm_bbox[2] - alarm_bbox[0]) - 2
            
            self.draw.text((alarm_x, 48), alarm_text, font=self.ampm_font, fill=255)
            self.draw.text((alarm_x - 12, 48), "A", font=self.ampm_font, fill=255)

    def adjust_window(self, increment):
        """Adjust wake window by increment"""
        self.wake_window_minutes += increment
        self.wake_window_minutes = max(0, min(90, self.wake_window_minutes))
        print(f"Wake window: {self.wake_window_minutes} minutes")
    
    def add_minutes(self, minutes):
        """Add minutes to the set time"""
        total_minutes = (self.set_hour * 60 + self.set_minute + minutes) % (24 * 60)
        self.set_hour = total_minutes // 60
        self.set_minute = total_minutes % 60
        self.set_is_pm = self.set_hour >= 12
    
    def reset_to_window_selection(self):
        """Reset all settings to their initial state"""
        self.interface_mode = 'WINDOW'
        self.wake_window_minutes = 30
        self.wake_window_fixed = False
        self.set_hour = 12
        self.set_minute = 0
        self.set_is_pm = True
        self.time_is_blinking = True
        self.set_time_fixed = False
        print("Reset to wake window selection. All settings cleared.")
    
    def confirm_window(self):
        """Confirm wake window and move to time setting"""
        self.wake_window_fixed = True
        self.interface_mode = 'TIME'
        self.time_is_blinking = True
        print(f"Wake window set to: {self.wake_window_minutes} minutes. Now set wake time.")
    
    def confirm_time(self):
        """Confirm the wake time and switch to clock mode"""
        # No more 'global' keyword needed
        self.set_time_fixed = True
        self.time_is_blinking = False
        self.interface_mode = 'CLOCK'
        
        today = datetime.date.today()
        set_datetime = datetime.datetime.combine(today, datetime.time(self.set_hour, self.set_minute))
        set_datetime -= datetime.timedelta(hours=9) # Convert from KST to UTC
        
        self.settime = set_datetime.timestamp()
        if self.settime <= time.time():
            self.settime += 24 * 60 * 60 # If time is in the past, set for tomorrow
        
        print("✅ Smart alarm fully configured!")
        print(f"✅ Monitoring will start {self.wake_window_minutes} minutes before wake time")
        
    def handle_gpioreset(self):
        while self.running:
            try:
                reset_state = GPIO.input(self.reset_pin)
                if self.last_reset_state == 1 and reset_state == 0:
                    self.reset_to_window_selection()
                self.last_reset_state = reset_state
                time.sleep(0.001)
            except Exception as e:
                print(f"GPIO error: {e}")
                time.sleep(0.01)

    def handle_gpio(self):
        """Handle GPIO inputs in a separate thread"""
        while self.running:
            try:
                reset_state = GPIO.input(self.reset_pin)
                if self.last_reset_state == 1 and reset_state == 0:
                    self.reset_to_window_selection()
                self.last_reset_state = reset_state
                
                set_state = GPIO.input(self.set_pin)
                if self.last_set_state == 1 and set_state == 0:
                    if self.interface_mode == 'WINDOW': self.confirm_window()
                    elif self.interface_mode == 'TIME': self.confirm_time()
                self.last_set_state = set_state
                
                clk_state = GPIO.input(self.CLK)
                if self.last_clk == 0 and clk_state == 1:
                    dt_state = GPIO.input(self.DT)
                    if self.interface_mode == 'WINDOW':
                        self.adjust_window(5 if dt_state == 0 else -5)
                    elif self.interface_mode == 'TIME':
                        self.add_minutes(5 if dt_state == 0 else -5)
                self.last_clk = clk_state
                
                time.sleep(0.001)
            except Exception as e:
                print(f"GPIO error: {e}")
                time.sleep(0.01)
    
    def run(self):
        """Main execution loop"""
        try:
            gpio_thread = threading.Thread(target=self.handle_gpio, daemon=True)
            gpio_thread.start()
            
            print("\nOLED Time Setter running...")
            print("Press Ctrl+C to stop")
            print("=" * 50)
            
            while not self.set_time_fixed:
                self.update_display()
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        self.oled.image(self.image)
        self.oled.show()
        print("Cleanup completed")

def main():
    system = OLEDTimeSetter()
    system.run()

if __name__ == "__main__":
    main()