#!/usr/bin/env python3
"""
Simple OLED Time Display
Minimal standalone script to show time on OLED display
"""

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

def main():
    # Initialize I2C and OLED
    i2c = busio.I2C(board.SCL, board.SDA)
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
    
    # Create image for drawing
    image = Image.new("1", (128, 64))
    draw = ImageDraw.Draw(image)
    
    # Load large font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = ImageFont.load_default()
    
    print("Displaying time... Press Ctrl+C to stop")
    
    try:
        while True:
            # Clear display
            draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
            
            # Get current time
            current_time = time.strftime("%I:%M:%S")
            ampm = time.strftime("%p")
            
            # Center the time on display
            bbox = draw.textbbox((0, 0), current_time, font=font)
            time_width = bbox[2] - bbox[0]
            time_x = (128 - time_width) // 2
            time_y = 15
            
            # Draw time
            draw.text((time_x, time_y), current_time, font=font, fill=255)
            
            # Draw AM/PM below time
            ampm_bbox = draw.textbbox((0, 0), ampm, font=font)
            ampm_width = ampm_bbox[2] - ampm_bbox[0]
            ampm_x = (128 - ampm_width) // 2
            draw.text((ampm_x, time_y + 25), ampm, font=font, fill=255)
            
            # Update display
            oled.image(image)
            oled.show()
            
            # Wait 1 second
            time.sleep(1)
            
    except KeyboardInterrupt:
        # Clear display when stopping
        draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
        oled.image(image)
        oled.show()
        print("\nTime display stopped")

if __name__ == "__main__":
    main()