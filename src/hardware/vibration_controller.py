#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibration Controller Module
Handles vibration motor control for the NeuroRise smart alarm system
"""

import time
import RPi.GPIO as GPIO

test = VibrationController()
test.start_alarm_vibration()

class VibrationController:
    def __init__(self, vibration_pin=27, reset_pin=4):
        """
        Initialize vibration controller
        
        Args:
            vibration_pin: GPIO pin for vibration motor (default: 27)
            reset_pin: GPIO pin for reset button (default: 4)
        """
        self.vibration_pin = vibration_pin
        self.reset_pin = reset_pin
        self.is_setup = False
        
    def setup_gpio(self):
        """Setup GPIO pins for vibration control"""
        if not self.is_setup:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            
            # Setup pins
            GPIO.setup(self.vibration_pin, GPIO.OUT)
            GPIO.setup(self.reset_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Initialize vibration as OFF
            GPIO.output(self.vibration_pin, GPIO.LOW)
            self.is_setup = True
            print(f"Vibration controller initialized - Pin {self.vibration_pin}")
    
    def vibrate_once(self, duration=1.0):
        """
        Single vibration pulse
        
        Args:
            duration: How long to vibrate in seconds (default: 1.0)
        """
        self.setup_gpio()
        GPIO.output(self.vibration_pin, GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(self.vibration_pin, GPIO.LOW)
    
    def is_reset_pressed(self, last_state):
        """
        Check if reset button was pressed (falling edge detection)
        
        Args:
            last_state: Previous button state
            
        Returns:
            tuple: (current_state, was_pressed)
        """
        current_state = GPIO.input(self.reset_pin)
        was_pressed = (last_state == 1 and current_state == 0)
        return current_state, was_pressed
    
    def start_alarm_vibration(self, vibrate_duration=1.0, pause_duration=0.2):
        """
        Start continuous vibration alarm that stops when reset button is pressed
        
        Args:
            vibrate_duration: How long each vibration lasts (default: 1.0s)
            pause_duration: Pause between vibrations (default: 0.2s)
        """
        self.setup_gpio()
        
        print("🚨 Smart Alarm Triggered! 🚨")
        print("Vibration alarm starting... Press reset button to stop.")
        
        try:
            alarm_active = True
            last_reset_state = GPIO.input(self.reset_pin)
            
            while alarm_active:
                # Check reset button before starting vibration
                current_reset_state, was_pressed = self.is_reset_pressed(last_reset_state)
                if was_pressed:
                    print("Reset button pressed - stopping alarm!")
                    break
                last_reset_state = current_reset_state
                
                # Start vibration
                print("Vibrating...")
                GPIO.output(self.vibration_pin, GPIO.HIGH)
                
                # Check for reset button during vibration (every 0.1s)
                vibration_checks = int(vibrate_duration / 0.1)
                for i in range(vibration_checks):
                    time.sleep(0.1)
                    current_reset_state, was_pressed = self.is_reset_pressed(last_reset_state)
                    if was_pressed:
                        print("Reset button pressed during vibration - stopping alarm!")
                        alarm_active = False
                        break
                    last_reset_state = current_reset_state
                
                if not alarm_active:
                    break
                
                # Stop vibration and pause
                GPIO.output(self.vibration_pin, GPIO.LOW)
                print("Pausing...")
                
                # Check for reset button during pause
                pause_checks = int(pause_duration / 0.1)
                for i in range(pause_checks):
                    time.sleep(0.1)
                    current_reset_state, was_pressed = self.is_reset_pressed(last_reset_state)
                    if was_pressed:
                        print("Reset button pressed during pause - stopping alarm!")
                        alarm_active = False
                        break
                    last_reset_state = current_reset_state
        
        except KeyboardInterrupt:
            print("\nAlarm interrupted by Ctrl+C")
        
        finally:
            # Always turn off vibration
            GPIO.output(self.vibration_pin, GPIO.LOW)
            print("Vibration alarm stopped.")
            print("Wake up time! Have a great day! ☀️")
    
    def stop_vibration(self):
        """Immediately stop vibration"""
        if self.is_setup:
            GPIO.output(self.vibration_pin, GPIO.LOW)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if self.is_setup:
            GPIO.output(self.vibration_pin, GPIO.LOW)
            # Note: Don't call GPIO.cleanup() here as other modules might be using GPIO


# Convenience functions for easy import
def trigger_vibration_alarm(vibrate_duration=1.0, pause_duration=0.2):
    """
    Convenience function to trigger vibration alarm
    
    Args:
        vibrate_duration: How long each vibration lasts (default: 1.0s)
        pause_duration: Pause between vibrations (default: 0.2s)
    """
    controller = VibrationController()
    controller.start_alarm_vibration(vibrate_duration, pause_duration)

def vibrate_once(duration=1.0, pin=27):
    """
    Convenience function for single vibration
    
    Args:
        duration: How long to vibrate (default: 1.0s)
        pin: GPIO pin for vibration motor (default: 27)
    """
    controller = VibrationController(vibration_pin=pin)
    controller.vibrate_once(duration)


if __name__ == "__main__":
    # Test the vibration controller
    print("Testing vibration controller...")
    trigger_vibration_alarm()