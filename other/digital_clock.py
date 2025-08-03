#!/usr/bin/env python3
"""
OLED Digital Clock
Displays a continuous digital clock on OLED display
Press Ctrl+C to stop
"""

import time
from OLED import OLEDDisplay

def main():
    """Run a continuous digital clock on OLED"""
    try:
        # Initialize OLED display
        print("Initializing OLED Digital Clock...")
        oled = OLEDDisplay()
        
        print("Digital clock started!")
        print("Press Ctrl+C to stop the clock")
        print("-" * 30)
        
        # Run continuous clock
        while True:
            oled.display_time_large(format_12hr=True)
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\nClock stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your OLED is connected properly and I2C is enabled.")
    finally:
        # Clear display and show goodbye message
        try:
            if 'oled' in locals():
                oled.display_text("Clock Stopped", 15, 25)
                time.sleep(2)
                oled.clear()
                print("Display cleared.")
        except:
            pass

if __name__ == "__main__":
    main()