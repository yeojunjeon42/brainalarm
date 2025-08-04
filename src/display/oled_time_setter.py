#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLED Time Setter System
Set time using rotary encoder and buttons, display on OLED
- Reset button: Reset to 12:00 PM
- Rotary encoder: Adjust time by 5-minute increments  
- Set button: Confirm time setting
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
settime_fixed = False  # Whether the time has been confirmed/set

class OLEDTimeSetter:
    def __init__(self):
        # GPIO Setup
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Pin definitions
        self.reset_pin = 4      # Was switch_pin, now resets time to 12:00 PM
        self.set_pin = 23       # Sets the time when pressed
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
        
        # Time setting variables (start at 12:00 PM)
        self.set_hour = 12
        self.set_minute = 0
        self.set_is_pm = True
        
        # Button state tracking
        self.last_reset_state = GPIO.input(self.reset_pin)
        self.last_set_state = GPIO.input(self.set_pin)
        
        # OLED Setup
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c)
        
        # Create image for drawing
        self.image = Image.new("1", (128, 64))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load large font for time display
        try:
            self.time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            self.ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            try:
                self.time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                self.ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                self.time_font = ImageFont.load_default()
                self.ampm_font = ImageFont.load_default()
        
        # System state
        self.running = True
        
        print("OLED Time Setter initialized")
        print("Reset pin: {} (resets to 12:00 PM)".format(self.reset_pin))
        print("Set pin: {} (sets the time)".format(self.set_pin))
        print("Rotary encoder: +/- 5 minutes per rotation")
    
    def update_display(self):
        """Update OLED display - shows only the set time"""
        # Clear display
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        
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
        
        # Update display
        self.oled.image(self.image)
        self.oled.show()
    
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
    
    def reset_time(self):
        """Reset time to 12:00 PM"""
        global settime_fixed
        
        self.set_hour = 12
        self.set_minute = 0
        self.set_is_pm = True
        settime_fixed = False  # Reset the fixed flag for smart alarm
        print("Time reset to 12:00 PM")
        print("⚠️  Wake time cleared - please set new time for smart alarm")
    
    def set_time(self):
        """Set the time and print confirmation"""
        global settime, settime_fixed
        
        display_hour = self.set_hour
        if display_hour == 0:
            display_hour = 12
        elif display_hour > 12:
            display_hour = display_hour - 12
        
        ampm = "PM" if self.set_is_pm else "AM"
        print("Time is successfully set to: {:02d}:{:02d} {}!".format(display_hour, self.set_minute, ampm))
        
        # Update global variables for smart alarm integration
        # Convert set time to today's datetime, then to unix timestamp
        today = datetime.date.today()
        set_datetime = datetime.datetime.combine(today, datetime.time(self.set_hour, self.set_minute))
        settime = set_datetime.timestamp()
        settime_fixed = True
        
        print("✅ Wake time set for smart alarm system!")

# Convenience functions for smart alarm integration
def get_set_time_info():
    """
    Get the current set time information for smart alarm integration
    
    Returns:
        dict: Contains settime (unix timestamp), settime_fixed (bool), 
              and formatted time info
    """
    if settime_fixed:
        set_dt = datetime.datetime.fromtimestamp(settime)
        return {
            'settime': settime,
            'settime_fixed': settime_fixed,
            'hour': set_dt.hour,
            'minute': set_dt.minute,
            'formatted': set_dt.strftime('%I:%M %p')
        }
    else:
        return {
            'settime': settime,
            'settime_fixed': False,
            'hour': None,
            'minute': None,
            'formatted': 'Not Set'
        }

def is_time_set():
    """Check if wake time has been set and confirmed"""
    return settime_fixed

class OLEDTimeSetter:
    def __init__(self):
        # GPIO Setup
        GPIO.cleanup()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Pin definitions
        self.reset_pin = 4      # Was switch_pin, now resets time to 12:00 PM
        self.set_pin = 23       # Sets the time when pressed
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
        
        # Time setting variables (start at 12:00 PM)
        self.set_hour = 12
        self.set_minute = 0
        self.set_is_pm = True
        
        # Button state tracking
        self.last_reset_state = GPIO.input(self.reset_pin)
        self.last_set_state = GPIO.input(self.set_pin)
        
        # OLED Setup
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, self.i2c)
        
        # Create image for drawing
        self.image = Image.new("1", (128, 64))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load large font for time display
        try:
            self.time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            self.ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            try:
                self.time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                self.ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                self.time_font = ImageFont.load_default()
                self.ampm_font = ImageFont.load_default()
        
        # System state
        self.running = True
        
        print("OLED Time Setter initialized")
        print("Reset pin: {} (resets to 12:00 PM)".format(self.reset_pin))
        print("Set pin: {} (sets the time)".format(self.set_pin))
        print("Rotary encoder: +/- 5 minutes per rotation")
    
    def update_display(self):
        """Update OLED display - shows only the set time"""
        # Clear display
        self.draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        
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
        
        # Update display
        self.oled.image(self.image)
        self.oled.show()
    
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
    
    def reset_time(self):
        """Reset time to 12:00 PM"""
        global settime_fixed
        
        self.set_hour = 12
        self.set_minute = 0
        self.set_is_pm = True
        settime_fixed = False  # Reset the fixed flag for smart alarm
        print("Time reset to 12:00 PM")
        print("⚠️  Wake time cleared - please set new time for smart alarm")
    
    def set_time(self):
        """Set the time and print confirmation"""
        global settime, settime_fixed
        
        display_hour = self.set_hour
        if display_hour == 0:
            display_hour = 12
        elif display_hour > 12:
            display_hour = display_hour - 12
        
        ampm = "PM" if self.set_is_pm else "AM"
        print("Time is successfully set to: {:02d}:{:02d} {}!".format(display_hour, self.set_minute, ampm))
        
        # Update global variables for smart alarm integration
        # Convert set time to today's datetime, then to unix timestamp
        today = datetime.date.today()
        set_datetime = datetime.datetime.combine(today, datetime.time(self.set_hour, self.set_minute))
        settime = set_datetime.timestamp()
        settime_fixed = True
        
        print("✅ Wake time set for smart alarm system!")

    def handle_gpio(self):
        """Handle GPIO inputs in separate thread"""
        while self.running:
            try:
                # Handle reset button (pin 4)
                reset_state = GPIO.input(self.reset_pin)
                if self.last_reset_state == 1 and reset_state == 0:  # Button pressed (falling edge)
                    self.reset_time()
                self.last_reset_state = reset_state
                
                # Handle set button (pin 23)
                set_state = GPIO.input(self.set_pin)
                if self.last_set_state == 1 and set_state == 0:  # Button pressed (falling edge)
                    self.set_time()
                self.last_set_state = set_state
                
                # Handle rotary encoder for time adjustment
                clk_state = GPIO.input(self.CLK)
                dt_state = GPIO.input(self.DT)
                
                # Only process on CLK rising edge (0 to 1)
                if self.last_clk == 0 and clk_state == 1:
                    # Direction detection based on DT state when CLK goes high
                    if dt_state == 0:
                        # Clockwise rotation - add 5 minutes
                        self.add_minutes(5)
                        print("Clockwise: +5 minutes")
                    else:
                        # Counter-clockwise rotation - subtract 5 minutes
                        self.add_minutes(-5)
                        print("Counter-clockwise: -5 minutes")
                
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
            print("Controls:")
            print("- Reset button (pin 4): Reset to 12:00 PM")
            print("- Rotary encoder: Clockwise +5min, Counter-clockwise -5min") 
            print("- Set button (pin 23): Confirm time setting")
            print("Press Ctrl+C to stop")
            print("=" * 40)
            
            # Show initial time
            self.update_display()
            
            # Main display update loop
            while self.running:
                self.update_display()
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

def main():
    system = OLEDTimeSetter()
    system.run()

if __name__ == "__main__":
    main()