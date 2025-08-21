#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLED Time Setter System
Set wake window and time using rotary encoder and buttons, display on OLED
- Reset button: Reset to window selection
- Rotary encoder: Adjust window (0-90 min) then time by 5-minute increments  
- Set button: Confirm window then confirm time setting
"""

import time
import threading
import datetime
import RPi.GPIO as GPIO
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

# Global variables for smart alarm integration
settime = time.time()  # Unix timestamp of set wake time
wake_window_minutes = 30  # Wake window in minutes (0-90)
wake_window_fixed = False  # Whether the wake window has been set


# Convenience functions for smart alarm integration
# def get_set_time_info():
#     """
#     Get the current set time information for smart alarm integration
    
#     Returns:
#         dict: Contains settime (unix timestamp), settime_fixed (bool), 
#               and formatted time info
#     """
#     if settime_fixed:
#         set_dt = datetime.datetime.fromtimestamp(settime)
#         return {
#             'settime': settime,
#             'settime_fixed': settime_fixed,
#             'hour': set_dt.hour,
#             'minute': set_dt.minute,
#             'formatted': set_dt.strftime('%I:%M %p')
#         }
#     else:
#         return {
#             'settime': settime,
#             'settime_fixed': False,
#             'hour': None,
#             'minute': None,
#             'formatted': 'Not Set'
#         }

class OLEDTimeSetter:
    def __init__(self):
        # GPIO Setup
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Pin definitions
        self.reset_pin = 4      # Resets to window selection
        self.set_pin = 23       # Sets the window/time when pressed
        self.vibration_pin = 27 # Not used in new functionality
        self.CLK = 17          # Rotary encoder clock
        self.DT = 18           # Rotary encoder data
        
        # Setup GPIO pins
        GPIO.setup(self.reset_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.set_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.vibration_pin, GPIO.OUT)
        GPIO.setup(self.CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Rotary encoder variables
        self.last_clk = GPIO.input(self.CLK)
        
        # Wake window setting variables (0-90 minutes in 5-minute increments)
        self.wake_window = 30  # Start at 30 minutes
        
        # Time setting variables (start at 12:00 PM)
        self.set_hour = 12
        self.set_minute = 0
        self.set_is_pm = True
        self.set_time_fixed = False  # Whether the time has been confirmed
        
        # Interface state management
        self.interface_mode = 'WINDOW'  # WINDOW, TIME
        self.time_is_blinking = True
        self.last_blink_time = time.time()
        self.blink_state = True
        
        # Button state tracking
        self.last_reset_state = GPIO.input(self.reset_pin)
        self.last_set_state = GPIO.input(self.set_pin)
        
        # OLED Setup
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c)
        
        # Create image for drawing
        self.image = Image.new("1", (128, 64))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts for display
        try:
            self.time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            self.ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            self.window_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        except:
            try:
                self.time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                self.ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                self.window_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                self.time_font = ImageFont.load_default()
                self.ampm_font = ImageFont.load_default()
                self.window_font = ImageFont.load_default()
        
        # System state
        self.running = True
        
        print("OLED Time Setter initialized")
        print("Interface: Wake window selection -> Time setting")
        print("Reset pin: {} (resets to window selection)".format(self.reset_pin))
        print("Set pin: {} (confirms window then time)".format(self.set_pin))
        print("Rotary encoder: Adjust window (0-90 min) then time (+/- 5 min)")
    
    def update_display(self):
        """Update OLED display based on current interface mode"""
        # Clear display
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        
        if self.interface_mode == 'WINDOW':
            self.draw_window_interface()
        elif self.interface_mode == 'TIME':
            self.draw_time_interface()
        
        # Update display
        self.oled.image(self.image)
        self.oled.show()
    
    def draw_window_interface(self):
        """Draw the wake window selection interface"""
        # Title
        title = "Wake Window"
        title_bbox = self.draw.textbbox((0, 0), title, font=self.ampm_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (128 - title_width) // 2
        self.draw.text((title_x, 5), title, font=self.ampm_font, fill=255)
        
        # Window value
        window_text = "{} mins".format(self.wake_window)
        window_bbox = self.draw.textbbox((0, 0), window_text, font=self.window_font)
        window_width = window_bbox[2] - window_bbox[0]
        window_x = (128 - window_width) // 2
        self.draw.text((window_x, 25), window_text, font=self.window_font, fill=255)
        
        # Instructions
        instr1 = "Rotate: 0-90 min"
        instr2 = "SET: Confirm"
        
        instr1_bbox = self.draw.textbbox((0, 0), instr1, font=self.ampm_font)
        instr1_width = instr1_bbox[2] - instr1_bbox[0]
        instr1_x = (128 - instr1_width) // 2
        self.draw.text((instr1_x, 48), instr1, font=self.ampm_font, fill=255)
        
        instr2_bbox = self.draw.textbbox((0, 0), instr2, font=self.ampm_font)
        instr2_width = instr2_bbox[2] - instr2_bbox[0]
        instr2_x = (128 - instr2_width) // 2
        self.draw.text((instr2_x, 58), instr2, font=self.ampm_font, fill=255)
    
    def draw_time_interface(self):
        """Draw the time setting interface with blinking"""
        # Check if we should blink
        current_time = time.time()
        if current_time - self.last_blink_time >= 1.0:  # 1 second intervals
            self.blink_state = not self.blink_state
            self.last_blink_time = current_time
        
        # Only draw time if not blinking or if blink state is True
        if not self.time_is_blinking or self.blink_state:
        # Format time as HH:MM AM/PM
            display_hour = self.set_hour
            if display_hour == 0:
                display_hour = 12
            elif display_hour > 12:
                display_hour = display_hour - 12
        
            time_text = "{:02d}:{:02d}".format(display_hour, self.set_minute)
            ampm_text = "PM" if self.set_is_pm else "AM"
            
            # Center the time text
            bbox = self.draw.textbbox((0, 0), time_text, font=self.time_font)
            time_width = bbox[2] - bbox[0]
            time_x = (128 - time_width) // 2
            time_y = 18  # Slightly higher for better centering
            
            # Draw time
            self.draw.text((time_x, time_y), time_text, font=self.time_font, fill=255)
            
            # Draw AM/PM below time
            ampm_bbox = self.draw.textbbox((0, 0), ampm_text, font=self.ampm_font)
            ampm_width = ampm_bbox[2] - ampm_bbox[0]
            ampm_x = (128 - ampm_width) // 2
            self.draw.text((ampm_x, time_y + 25), ampm_text, font=self.ampm_font, fill=255)
            
            # Show window info at bottom
            window_info = "{}min before".format(self.wake_window)
            window_bbox = self.draw.textbbox((0, 0), window_info, font=self.ampm_font)
            window_width = window_bbox[2] - window_bbox[0]
            window_x = (128 - window_width) // 2
            self.draw.text((window_x, 54), window_info, font=self.ampm_font, fill=255)
    
    def adjust_window(self, increment):
        """Adjust wake window by increment (in 5-minute steps)"""
        self.wake_window += increment
        
        # Constrain to 0-90 minutes
        if self.wake_window < 0:
            self.wake_window = 0
        elif self.wake_window > 90:
            self.wake_window = 90
        
        print("Wake window: {} minutes".format(self.wake_window))
    
    def add_minutes(self, minutes):
        """Add minutes to the set time"""
        total_minutes = self.set_hour * 60 + self.set_minute + minutes
        
        # Handle negative wrap-around
        if total_minutes < 0:
            total_minutes = (24 * 60) + total_minutes
        
        # Handle positive wrap-around
        total_minutes = total_minutes % (24 * 60)
        
        # Convert back to hours and minutes
        self.set_hour = total_minutes // 60
        self.set_minute = total_minutes % 60
        
        # Determine AM/PM
        if self.set_hour >= 12:
            self.set_is_pm = True
        else:
            self.set_is_pm = False
    
    def reset_to_window_selection(self):
        """Reset to window selection interface"""
        global  wake_window_fixed
        
        self.interface_mode = 'WINDOW'
        self.wake_window = 30  # Reset to default 30 minutes
        self.set_hour = 12
        self.set_minute = 0
        self.set_is_pm = True
        self.time_is_blinking = True
        
        self.set_time_fixed = False
        wake_window_fixed = False
        
        print("Reset to wake window selection")
        print("⚠️  All settings cleared - please set window and time")
    
    def confirm_window(self):
        """Confirm wake window and move to time setting"""
        global wake_window_minutes, wake_window_fixed
        
        wake_window_minutes = self.wake_window
        wake_window_fixed = True
        self.interface_mode = 'TIME'
        self.time_is_blinking = True  # Start blinking when entering time mode
        
        print("Wake window set to: {} minutes before wake time".format(self.wake_window))
        print("Now set your desired wake time")
    
    def confirm_time(self):
        """Confirm the wake time and finish setup"""
        global settime
        
        display_hour = self.set_hour
        if display_hour == 0:
            display_hour = 12
        elif display_hour > 12:
            display_hour = display_hour - 12
        
        ampm = "PM" if self.set_is_pm else "AM"
        print("Wake time set to: {:02d}:{:02d} {}!".format(display_hour, self.set_minute, ampm))
        print("Smart alarm will monitor {} minutes before this time".format(self.wake_window))
        
        # Update global variables for smart alarm integration
        today = datetime.date.today()

        #set_datetime이 기존에 당일 몇 시에 대해서만 설정 가능
        set_datetime = datetime.datetime.combine(today, datetime.time(self.set_hour, self.set_minute))
        settime = set_datetime.timestamp()
        self.set_time_fixed = True
        
        # Stop blinking since time is now set
        self.time_is_blinking = False
        
        print("✅ Smart alarm fully configured!")
        print("✅ Monitoring will start {} minutes before wake time".format(self.wake_window))

    def handle_gpio(self):
        """Handle GPIO inputs in separate thread"""
        while self.running:
            try:
                if self.set_time_fixed:
                    time.sleep(0.1)
                    continue  # Skip GPIO handling if time is already set
                # Handle reset button (pin 4)
                reset_state = GPIO.input(self.reset_pin)
                if self.last_reset_state == 1 and reset_state == 0:  # Button pressed (falling edge)
                    self.reset_to_window_selection()
                self.last_reset_state = reset_state
                
                # Handle set button (pin 23)
                set_state = GPIO.input(self.set_pin)
                if self.last_set_state == 1 and set_state == 0:  # Button pressed (falling edge)
                    if self.interface_mode == 'WINDOW':
                        self.confirm_window()
                    elif self.interface_mode == 'TIME':
                        self.confirm_time()
                self.last_set_state = set_state
                
                # Handle rotary encoder
                clk_state = GPIO.input(self.CLK)
                dt_state = GPIO.input(self.DT)
                
                # Only process on CLK rising edge (0 to 1)
                if self.last_clk == 0 and clk_state == 1:
                    # Direction detection based on DT state when CLK goes high
                    if dt_state == 0:
                        # Clockwise rotation
                        if self.interface_mode == 'WINDOW':
                            self.adjust_window(5)  # +5 minutes for window
                            print("Clockwise: +5 minutes window")
                        elif self.interface_mode == 'TIME':
                            self.add_minutes(5)  # +5 minutes for time
                            print("Clockwise: +5 minutes time")
                    else:
                        # Counter-clockwise rotation
                        if self.interface_mode == 'WINDOW':
                            self.adjust_window(-5)  # -5 minutes for window
                            print("Counter-clockwise: -5 minutes window")
                        elif self.interface_mode == 'TIME':
                            self.add_minutes(-5)  # -5 minutes for time
                            print("Counter-clockwise: -5 minutes time")
                
                self.last_clk = clk_state
                time.sleep(0.001)
                
            except Exception as e:
                print("GPIO error: {}".format(str(e)))
                time.sleep(0.01)
    
    def run(self):
        """Main execution loop"""
        try:
            # Start GPIO handling in separate thread
            gpio_thread = threading.Thread(target=self.handle_gpio, daemon=True)
            gpio_thread.start()
            
            print("\nOLED Time Setter running...")
            print("Interface Flow:")
            print("1. Set wake window (0-90 minutes)")
            print("2. Set wake time")
            print("Controls:")
            print("- Reset button (pin 4): Reset to window selection")
            print("- Rotary encoder: Adjust window/time") 
            print("- Set button (pin 23): Confirm window then time")
            print("Press Ctrl+C to stop")
            print("=" * 50)
            
            # Show initial display
            self.update_display()
            
            # Main display update loop
            while self.running:
                self.update_display()
                if self.set_time_fixed:
                    # 시간이 설정되었다면, 3초간 최종 시간을 보여주고 종료
                    time.sleep(3)
                    self.running = False # 루프 종료 신호
                else:
                    # 시간이 설정되지 않았다면, 0.1초 대기
                    time.sleep(0.1)
                time.sleep(0.1)  # Update display 10 times per second
                
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print("Error: {}".format(str(e)))
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        # Clear OLED
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        self.oled.image(self.image)
        self.oled.show()
        
        # Clean up GPIO
        GPIO.cleanup()
        print("Cleanup completed")


def get_wake_window():
    """Get the wake window in minutes"""
    return wake_window_minutes

def is_wake_window_set():
    """Check if wake window has been set"""
    return wake_window_fixed

def main():
    system = OLEDTimeSetter()
    system.run()

if __name__ == "__main__":
    main()
