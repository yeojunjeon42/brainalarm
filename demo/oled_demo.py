#!/usr/bin/env python3
"""
NeuroRise Smart Alarm - OLED Demo
=================================

Combined demo featuring:
1. Full alarm setting with rotary encoder and OLED display
2. Vibration motor control with terminal input
3. Reset button to stop vibration

Uses functions from oled_time_setter.py and vibration_controller.py
"""

import time
import threading
import sys
import os

# Add paths to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from display.oled_time_setter import OLEDTimeSetter, get_set_time_info, is_time_set
    from hardware.vibration_controller import VibrationController, trigger_vibration_alarm, vibrate_once
    HARDWARE_AVAILABLE = True
    print("✅ All modules loaded successfully!")
except ImportError as e:
    print(f"⚠️  Hardware not available: {e}")
    print("This demo requires Raspberry Pi with GPIO pins and OLED display.")
    HARDWARE_AVAILABLE = False

class OLEDDemo:
    def __init__(self):
        """Initialize the OLED demo system"""
        if not HARDWARE_AVAILABLE:
            print("❌ Cannot initialize - hardware modules not available")
            return
            
        print("🧠 NeuroRise OLED Demo - Initializing...")
        
        # Initialize OLED time setter
        self.oled_system = OLEDTimeSetter()
        
        # Initialize vibration controller
        self.vibration_controller = VibrationController()
        
        # Demo state
        self.running = True
        self.vibration_active = False
        
        print("✅ OLED Demo initialized!")
        print("📱 OLED Display: Time setting interface")
        print("🔧 Rotary Encoder: Adjust time (+/- 5 minutes)")
        print("🔴 Reset Button (pin 4): Stop vibration")
        print("🟢 Set Button (pin 23): Confirm time")
        print("📳 Vibration Motor: Terminal controlled")
    
    def show_menu(self):
        """Display the main menu"""
        print("\n" + "="*50)
        print("🧠 NeuroRise OLED Demo Menu")
        print("="*50)
        print("1. 🕐 Set Alarm Time (OLED + Rotary Encoder)")
        print("2. 📳 Test Vibration Motor")
        print("3. 🚨 Full Alarm Test (Time + Vibration)")
        print("4. 🔍 Show Current Time Setting")
        print("5. 🔧 Hardware Test (All Components)")
        print("6. ❌ Exit")
        print("="*50)
    
    def set_alarm_time(self):
        """Run the alarm time setting interface"""
        print("\n🕐 Alarm Time Setting Mode")
        print("="*30)
        print("📱 Use the OLED display and rotary encoder to set time")
        print("🔧 Turn encoder: Clockwise +5min, Counter-clockwise -5min")
        print("🟢 Press SET button (pin 23) to confirm time")
        print("🔴 Press RESET button (pin 4) to reset to 12:00 PM")
        print("💻 Press Ctrl+C in terminal to return to menu")
        print("="*30)
        
        try:
            # Start the OLED time setter
            self.oled_system.run()
        except KeyboardInterrupt:
            print("\n⏹️  Time setting stopped - returning to menu")
            self.oled_system.cleanup()
            # Reinitialize for next use
            self.oled_system = OLEDTimeSetter()
    
    def test_vibration(self):
        """Test vibration motor with terminal control"""
        print("\n📳 Vibration Motor Test")
        print("="*25)
        print("💻 Commands:")
        print("  'start' - Start vibration")
        print("  'stop' - Stop vibration")
        print("  'pulse' - Single vibration pulse")
        print("  'alarm' - Start alarm pattern")
        print("  'quit' - Return to menu")
        print("🔴 Press RESET button (pin 4) to stop any vibration")
        print("="*25)
        
        while True:
            try:
                command = input("Enter command: ").strip().lower()
                
                if command == 'start':
                    print("📳 Starting continuous vibration...")
                    self.vibration_controller.setup_gpio()
                    self.vibration_controller.vibrate_once(duration=999)  # Long duration
                    self.vibration_active = True
                    
                elif command == 'stop':
                    print("⏹️  Stopping vibration...")
                    self.vibration_controller.stop_vibration()
                    self.vibration_active = False
                    
                elif command == 'pulse':
                    print("📳 Single vibration pulse...")
                    vibrate_once(duration=1.0)
                    
                elif command == 'alarm':
                    print("🚨 Starting alarm pattern...")
                    print("💡 Press RESET button (pin 4) to stop alarm")
                    trigger_vibration_alarm(vibrate_duration=1.0, pause_duration=0.2)
                    
                elif command == 'quit':
                    print("⏹️  Returning to menu...")
                    if self.vibration_active:
                        self.vibration_controller.stop_vibration()
                    break
                    
                else:
                    print("❌ Unknown command. Try: start, stop, pulse, alarm, quit")
                    
            except KeyboardInterrupt:
                print("\n⏹️  Vibration test stopped")
                if self.vibration_active:
                    self.vibration_controller.stop_vibration()
                break
    
    def full_alarm_test(self):
        """Test the complete alarm system"""
        print("\n🚨 Full Alarm System Test")
        print("="*30)
        
        # Check if time is set
        time_info = get_set_time_info()
        if not time_info['settime_fixed']:
            print("⚠️  No alarm time set! Please set time first.")
            print("💡 Use option 1 to set alarm time")
            return
        
        print(f"⏰ Alarm time: {time_info['formatted']}")
        print("📳 Starting vibration alarm...")
        print("🔴 Press RESET button (pin 4) to stop alarm")
        print("="*30)
        
        try:
            trigger_vibration_alarm(vibrate_duration=1.0, pause_duration=0.2)
        except KeyboardInterrupt:
            print("\n⏹️  Alarm test stopped by user")
    
    def show_current_time(self):
        """Display current time setting"""
        print("\n🔍 Current Time Setting")
        print("="*25)
        
        time_info = get_set_time_info()
        if time_info['settime_fixed']:
            print(f"⏰ Alarm time: {time_info['formatted']}")
            print(f"🕐 24h format: {time_info['hour']:02d}:{time_info['minute']:02d}")
            print(f"📅 Unix timestamp: {time_info['settime']}")
        else:
            print("⚠️  No alarm time set")
            print("💡 Use option 1 to set alarm time")
    
    def hardware_test(self):
        """Test all hardware components"""
        print("\n🔧 Hardware Component Test")
        print("="*30)
        
        # Test OLED display
        print("📱 Testing OLED display...")
        try:
            self.oled_system.update_display()
            print("✅ OLED display working")
        except Exception as e:
            print(f"❌ OLED display error: {e}")
        
        # Test vibration motor
        print("📳 Testing vibration motor...")
        try:
            vibrate_once(duration=0.5)
            print("✅ Vibration motor working")
        except Exception as e:
            print(f"❌ Vibration motor error: {e}")
        
        # Test reset button
        print("🔴 Testing reset button (press button within 20 seconds)...")
        try:
            import RPi.GPIO as GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            start_time = time.time()
            last_state = GPIO.input(4)
            press_count = 0
            
            while time.time() - start_time < 20:
                current_state = GPIO.input(4)
                if last_state == 1 and current_state == 0:
                    press_count += 1
                    print(f"🔴 Button pressed! (count: {press_count})")
                last_state = current_state
                time.sleep(0.05)
            
            if press_count > 0:
                print(f"✅ Reset button working ({press_count} presses detected)")
            else:
                print("⚠️  No button presses detected - check wiring")
            
            GPIO.cleanup()
        except Exception as e:
            print(f"❌ Reset button error: {e}")
        
        print("🔧 Hardware test completed!")
    
    def run(self):
        """Main demo loop"""
        if not HARDWARE_AVAILABLE:
            print("❌ Demo not available - hardware modules not found")
            return
        
        print("🧠 NeuroRise OLED Demo Started!")
        print("💡 This demo combines time setting and vibration control")
        
        while self.running:
            try:
                self.show_menu()
                choice = input("\nSelect option (1-6): ").strip()
                
                if choice == '1':
                    self.set_alarm_time()
                elif choice == '2':
                    self.test_vibration()
                elif choice == '3':
                    self.full_alarm_test()
                elif choice == '4':
                    self.show_current_time()
                elif choice == '5':
                    self.hardware_test()
                elif choice == '6':
                    print("👋 Exiting demo...")
                    self.running = False
                else:
                    print("❌ Invalid choice, please select 1-6")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Demo stopped by user")
                self.running = False
            except Exception as e:
                print(f"❌ Demo error: {e}")
        
        # Cleanup
        try:
            self.oled_system.cleanup()
            if hasattr(self, 'vibration_controller'):
                self.vibration_controller.cleanup()
        except:
            pass
        print("✅ Demo cleanup completed")

def main():
    """Main entry point"""
    demo = OLEDDemo()
    demo.run()

if __name__ == "__main__":
    main()
