#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple OLED Test - No GPIO, just display test
This helps isolate OLED display issues from GPIO issues
"""

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

def main():
    try:
        print("Starting simple OLED test...")
        
        # Initialize I2C and OLED
        i2c = busio.I2C(board.SCL, board.SDA)
        oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
        
        # Create image for drawing
        image = Image.new("1", (128, 64))
        draw = ImageDraw.Draw(image)
        
        # Load font with error handling
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            print("Font loaded successfully")
        except Exception as e:
            font = ImageFont.load_default()
            print("Using default font due to error: {}".format(str(e)))
        
        print("OLED initialized successfully")
        
        # Test 1: Simple text
        draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        draw.text((10, 10), "OLED Test OK", font=font, fill=255)
        oled.image(image)
        oled.show()
        print("Test 1: Simple text - OK")
        time.sleep(2)
        
        # Test 2: Time display
        draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        current_time = time.strftime("%H:%M:%S")
        draw.text((25, 25), current_time, font=font, fill=255)
        oled.image(image)
        oled.show()
        print("Test 2: Time display - OK")
        time.sleep(2)
        
        # Test 3: Clear display
        draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        oled.image(image)
        oled.show()
        print("Test 3: Clear display - OK")
        
        print("All OLED tests passed!")
        
    except Exception as e:
        print("OLED test failed with error: {}".format(str(e)))
        print("Check I2C connection and OLED wiring")

if __name__ == "__main__":
    main()