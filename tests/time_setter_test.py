#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Time Setter Test - Test OLED display without GPIO
Tests the time display formatting and font sizing
"""

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

def test_time_display():
    try:
        print("Testing OLED time display...")
        
        # Initialize I2C and OLED
        i2c = busio.I2C(board.SCL, board.SDA)
        oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
        
        # Create image for drawing
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        
        # Load large fonts like the main program
        try:
            time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            print("Large fonts loaded successfully")
        except:
            try:
                time_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                ampm_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                print("Medium fonts loaded successfully")
            except:
                time_font = ImageFont.load_default()
                ampm_font = ImageFont.load_default()
                print("Using default fonts")
        
        # Test different times
        test_times = [
            (12, 0, True),   # 12:00 PM
            (1, 30, False),  # 01:30 AM
            (11, 45, True),  # 11:45 PM
            (6, 15, False)   # 06:15 AM
        ]
        
        for hour, minute, is_pm in test_times:
            # Clear display
            draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
            
            # Format time
            display_hour = hour
            if display_hour == 0:
                display_hour = 12
            elif display_hour > 12:
                display_hour = display_hour - 12
            
            time_text = "{:02d}:{:02d}".format(display_hour, minute)
            ampm_text = "PM" if is_pm else "AM"
            
            # Center the time text
            bbox = draw.textbbox((0, 0), time_text, font=time_font)
            time_width = bbox[2] - bbox[0]
            time_x = (128 - time_width) // 2
            time_y = 18
            
            # Draw time
            draw.text((time_x, time_y), time_text, font=time_font, fill=255)
            
            # Draw AM/PM below time
            ampm_bbox = draw.textbbox((0, 0), ampm_text, font=ampm_font)
            ampm_width = ampm_bbox[2] - ampm_bbox[0]
            ampm_x = (128 - ampm_width) // 2
            draw.text((ampm_x, time_y + 25), ampm_text, font=ampm_font, fill=255)
            
            # Update display
            oled.image(image)
            oled.show()
            
            print("Displaying: {} {}".format(time_text, ampm_text))
            time.sleep(3)
        
        # Clear display
        draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        oled.image(image)
        oled.show()
        
        print("Time display test completed successfully!")
        
    except Exception as e:
        print("Error during time display test: {}".format(str(e)))

if __name__ == "__main__":
    test_time_display()