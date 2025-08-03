#!/usr/bin/env python3
"""
NeuroRise Smart Alarm - Vibration Wake-up Demo
==============================================

Demo of the vibration wake-up process using REAL HARDWARE.
Tests the actual vibration controller and GPIO pins on Raspberry Pi.
"""

import time
import random
import sys
import os

# Add paths to import our hardware modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'hardware'))

try:
    from vibration_controller import VibrationController, trigger_vibration_alarm, vibrate_once
    HARDWARE_AVAILABLE = True
    print("✅ Hardware modules loaded successfully!")
except ImportError as e:
    print(f"⚠️  Hardware not available: {e}")
    print("This demo requires Raspberry Pi with GPIO pins.")
    HARDWARE_AVAILABLE = False

def test_vibration_wake_up():
    """Test the vibration alarm wake-up process with REAL HARDWARE"""
    if not HARDWARE_AVAILABLE:
        print("❌ Cannot run hardware test - RPi.GPIO not available")
        return
    
    print("🧠 NeuroRise Smart Alarm - HARDWARE TEST")
    print("="*45)
    print("💤 N2 sleep stage detected!")
    print("⏰ Optimal wake time reached")
    print("📳 Starting REAL vibration alarm...")
    print("🔴 Press RESET BUTTON (pin 4) to stop alarm!")
    print("="*45)
    
    try:
        # Use the actual vibration alarm function from our hardware module
        trigger_vibration_alarm(vibrate_duration=1.0, pause_duration=0.2)
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo stopped by Ctrl+C")
    except Exception as e:
        print(f"\n❌ Hardware error: {e}")
        print("Check GPIO connections and permissions!")

def test_single_vibration():
    """Test single vibration pulse with REAL HARDWARE"""
    if not HARDWARE_AVAILABLE:
        print("❌ Cannot run hardware test - RPi.GPIO not available")
        return
        
    print("\n" + "="*45)
    print("🔴 Single Vibration Test")
    print("="*45)
    print("📳 Testing vibration motor for 2 seconds...")
    
    try:
        # Test single vibration pulse
        vibrate_once(duration=2.0)
        print("✅ Vibration test completed!")
        
    except Exception as e:
        print(f"❌ Hardware error: {e}")
        print("Check vibration motor connection on pin 27!")

def test_button_reading():
    """Test reading the reset button state"""
    if not HARDWARE_AVAILABLE:
        print("❌ Cannot run hardware test - RPi.GPIO not available")
        return
        
    print("\n" + "="*45)
    print("🔴 Reset Button Test")
    print("="*45)
    print("Press and hold RESET BUTTON (pin 4) - monitoring for 10 seconds...")
    
    try:
        import RPi.GPIO as GPIO
        
        # Setup button pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        start_time = time.time()
        last_state = GPIO.input(4)
        press_count = 0
        
        while time.time() - start_time < 10:
            current_state = GPIO.input(4)
            
            if last_state == 1 and current_state == 0:
                press_count += 1
                print(f"🔴 Button pressed! (count: {press_count})")
            elif last_state == 0 and current_state == 1:
                print("🔴 Button released!")
                
            last_state = current_state
            time.sleep(0.1)
        
        print(f"✅ Button test completed! Total presses: {press_count}")
        
    except Exception as e:
        print(f"❌ Hardware error: {e}")
        print("Check button connection on pin 4!")

def main():
    """Run hardware vibration tests"""
    print("🧠 NeuroRise Hardware Test Demos")
    print("="*40)
    
    if not HARDWARE_AVAILABLE:
        print("❌ Hardware not available!")
        print("This demo requires:")
        print("  - Raspberry Pi with GPIO pins")
        print("  - Vibration motor on pin 27") 
        print("  - Reset button on pin 4")
        print("  - RPi.GPIO Python library")
        return
    
    print("Available hardware tests:")
    print("1. 🚨 Full smart alarm test (vibration + reset button)")
    print("2. 📳 Single vibration pulse test") 
    print("3. 🔴 Reset button test")
    print("4. 🔧 All hardware tests")
    print("5. ❌ Exit")
    
    try:
        choice = input("\nSelect test (1-5): ").strip()
        
        if choice == '1':
            print("\n🚨 Starting full alarm test...")
            print("💡 TIP: Press reset button (pin 4) to stop the alarm!")
            input("Press Enter when ready...")
            test_vibration_wake_up()
            
        elif choice == '2':
            print("\n📳 Testing single vibration...")
            input("Press Enter to start vibration test...")
            test_single_vibration()
            
        elif choice == '3':
            print("\n🔴 Testing reset button...")
            input("Press Enter to start button test...")
            test_button_reading()
            
        elif choice == '4':
            print("\n🔧 Running all hardware tests...")
            input("Press Enter to start...")
            test_single_vibration()
            time.sleep(2)
            test_button_reading() 
            time.sleep(2)
            print("\n🚨 Finally, testing full alarm...")
            input("Press Enter for full alarm test...")
            test_vibration_wake_up()
            
        elif choice == '5':
            print("👋 Exiting...")
            
        else:
            print("❌ Invalid choice, running single vibration test...")
            test_single_vibration()
            
    except KeyboardInterrupt:
        print("\n\n👋 Tests stopped by user")

if __name__ == "__main__":
    main()
