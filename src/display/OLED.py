#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OLED Display Module
Provides a simple interface for OLED display operations
"""

import time
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

class OLEDDisplay:
    def __init__(self, width=128, height=64):
        """Initialize OLED display"""
        self.width = width
        self.height = height
        
        # Initialize I2C and OLED
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(width, height, self.i2c)
        
        # Create image for drawing
        self.image = Image.new("1", (width, height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts
        self._load_fonts()
        
        # Clear display initially
        self.clear()
    
    def _load_fonts(self):
        """Load fonts for display"""
        try:
            self.large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            self.medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            self.small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            try:
                self.large_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
                self.medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                self.small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            except:
                self.large_font = ImageFont.load_default()
                self.medium_font = ImageFont.load_default()
                self.small_font = ImageFont.load_default()
    
    def clear(self):
        """Clear the display"""
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
        self.oled.image(self.image)
        self.oled.show()
    
    def display_text(self, text, x=None, y=None, font_size="medium", center=True):
        """Display text on OLED
        
        Args:
            text: Text to display
            x, y: Position (if None and center=True, will center text)
            font_size: "small", "medium", or "large"
            center: Whether to center the text if x,y not provided
        """
        self.clear()
        
        # Select font
        if font_size == "large":
            font = self.large_font
        elif font_size == "small":
            font = self.small_font
        else:
            font = self.medium_font
        
        # Calculate position
        if x is None or y is None:
            if center:
                bbox = self.draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self.width - text_width) // 2 if x is None else x
                y = (self.height - text_height) // 2 if y is None else y
            else:
                x = x or 0
                y = y or 0
        
        # Draw text
        self.draw.text((x, y), text, font=font, fill=255)
        self.oled.image(self.image)
        self.oled.show()
    
    def display_time_large(self, format_12hr=True):
        """Display current time in large format"""
        current_time = time.strftime("%I:%M:%S" if format_12hr else "%H:%M:%S")
        ampm = time.strftime("%p") if format_12hr else ""
        
        self.clear()
        
        # Draw time
        bbox = self.draw.textbbox((0, 0), current_time, font=self.large_font)
        time_width = bbox[2] - bbox[0]
        time_x = (self.width - time_width) // 2
        time_y = 15
        
        self.draw.text((time_x, time_y), current_time, font=self.large_font, fill=255)
        
        # Draw AM/PM if 12-hour format
        if format_12hr and ampm:
            ampm_bbox = self.draw.textbbox((0, 0), ampm, font=self.medium_font)
            ampm_width = ampm_bbox[2] - ampm_bbox[0]
            ampm_x = (self.width - ampm_width) // 2
            self.draw.text((ampm_x, time_y + 25), ampm, font=self.medium_font, fill=255)
        
        self.oled.image(self.image)
        self.oled.show()
    
    def display_time_setting(self, hour, minute, is_pm=True):
        """Display time setting interface"""
        display_hour = hour
        if display_hour == 0:
            display_hour = 12
        elif display_hour > 12:
            display_hour = display_hour - 12
        
        time_text = "{:02d}:{:02d}".format(display_hour, minute)
        ampm_text = "PM" if is_pm else "AM"
        
        self.clear()
        
        # Center the time text
        bbox = self.draw.textbbox((0, 0), time_text, font=self.large_font)
        time_width = bbox[2] - bbox[0]
        time_x = (self.width - time_width) // 2
        time_y = 18
        
        # Draw time
        self.draw.text((time_x, time_y), time_text, font=self.large_font, fill=255)
        
        # Draw AM/PM below time
        ampm_bbox = self.draw.textbbox((0, 0), ampm_text, font=self.medium_font)
        ampm_width = ampm_bbox[2] - ampm_bbox[0]
        ampm_x = (self.width - ampm_width) // 2
        self.draw.text((ampm_x, time_y + 25), ampm_text, font=self.medium_font, fill=255)
        
        self.oled.image(self.image)
        self.oled.show()