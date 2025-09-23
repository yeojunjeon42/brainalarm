#!/usr/bin/env python3
"""
Rotary Encoder Test for Raspberry Pi 4B
Pins: switch=23, clk=17, dt=18
"""

import RPi.GPIO as GPIO
import time
import sys

class RotaryEncoder:
    def __init__(self, switch_pin=23, clk_pin=17, dt_pin=18):
        self.switch_pin = switch_pin
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        
        # Encoder state
        self.counter = 0
        self.last_clk_state = 0
        self.last_dt_state = 0
        self.last_switch_state = 0
        
        # Setup GPIO
        self.setup_gpio()
        
    def setup_gpio(self):
        """Initialize GPIO pins for rotary encoder"""
        GPIO.setmode(GPIO.BCM)
        
        # Set up pins with pull-up resistors
        GPIO.setup(self.switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Read initial states
        self.last_clk_state = GPIO.input(self.clk_pin)
        self.last_dt_state = GPIO.input(self.dt_pin)
        self.last_switch_state = GPIO.input(self.switch_pin)
        
        print(f"GPIO initialized - Switch: {self.switch_pin}, CLK: {self.clk_pin}, DT: {self.dt_pin}")
        print(f"Initial states - Switch: {self.last_switch_state}, CLK: {self.last_clk_state}, DT: {self.last_dt_state}")
        
    def read_encoder(self):
        """Read encoder rotation and button press"""
        # Read current states
        clk_state = GPIO.input(self.clk_pin)
        dt_state = GPIO.input(self.dt_pin)
        switch_state = GPIO.input(self.switch_pin)
        
        # Check for rotation
        if clk_state != self.last_clk_state:
            # CLK pin changed, check DT pin to determine direction
            if dt_state != clk_state:
                # Clockwise rotation
                self.counter += 1
                print(f"Clockwise rotation - Counter: {self.counter}")
            else:
                # Counter-clockwise rotation
                self.counter -= 1
                print(f"Counter-clockwise rotation - Counter: {self.counter}")
        
        # Check for button press (falling edge)
        if switch_state == 0 and self.last_switch_state == 1:
            print(f"Button pressed! Counter reset to 0")
            self.counter = 0
        
        # Update last states
        self.last_clk_state = clk_state
        self.last_dt_state = dt_state
        self.last_switch_state = switch_state
        
        return self.counter
    
    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup()
        print("GPIO cleaned up")

def main():
    """Main test function"""
    print("Rotary Encoder Test Starting...")
    print("Press Ctrl+C to exit")
    print("-" * 40)
    
    try:
        # Create encoder instance
        encoder = RotaryEncoder(switch_pin=23, clk_pin=17, dt_pin=18)
        
        print("Rotary encoder ready!")
        print("Turn the encoder to see counter changes")
        print("Press the encoder button to reset counter")
        print("-" * 40)
        
        # Main loop
        while True:
            counter = encoder.read_encoder()
            time.sleep(0.01)  # Small delay to prevent excessive CPU usage
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        encoder.cleanup()
        print("Test completed")

if __name__ == "__main__":
    main()
