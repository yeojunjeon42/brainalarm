#!/usr/bin/env python3
"""
NeuroRise Smart Alarm System - Main Application
==============================================

Complete NeuroRise smart alarm system that integrates:
- OLED time setting with rotary encoder
- EEG signal processing and sleep stage detection  
- Smart alarm with vibration motor
- Hardware controls and monitoring

Hardware Requirements:
- Raspberry Pi with GPIO
- OLED Display (SSD1306 128x64)
- Rotary encoder (pins 17, 18)
- Reset button (pin 4)
- Set button (pin 23) 
- Vibration motor (pin 27)
- EEG sensor input
"""

import sys
import os
import time
import datetime
import threading
import signal
from pathlib import Path

# Add all source paths
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR / 'src'))
sys.path.append(str(BASE_DIR / 'src' / 'alarm'))
sys.path.append(str(BASE_DIR / 'src' / 'display'))
sys.path.append(str(BASE_DIR / 'src' / 'hardware'))
sys.path.append(str(BASE_DIR / 'src' / 'processing'))

# Import system modules with individual error handling
HARDWARE_AVAILABLE = True
OLED_AVAILABLE = False
VIBRATION_AVAILABLE = False
PROCESSING_AVAILABLE = False
XGBOOST_AVAILABLE = False
GPIO_AVAILABLE = False

print("🔍 Checking NeuroRise module availability...")

# Check GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    print("✅ RPi.GPIO loaded")
except ImportError:
    print("❌ RPi.GPIO not available")

# Check OLED system
try:
    from display.oled_time_setter import OLEDTimeSetter, get_set_time_info, is_time_set
    OLED_AVAILABLE = True
    print("✅ OLED display system loaded")
except ImportError as e:
    print(f"❌ OLED system not available: {e}")

# Check vibration controller
try:
    from hardware.vibration_controller import VibrationController, trigger_vibration_alarm
    VIBRATION_AVAILABLE = True
    print("✅ Vibration controller loaded")
except ImportError as e:
    print(f"❌ Vibration controller not available: {e}")

# Check signal processing
try:
    from processing.feature_extract import exfeature
    from processing.signal_processing import filter_bandpass
    PROCESSING_AVAILABLE = True
    print("✅ Signal processing loaded")
except ImportError as e:
    print(f"❌ Signal processing not available: {e}")

# Check XGBoost (optional)
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
    print("✅ XGBoost loaded")
except ImportError:
    print("⚠️  XGBoost not available - using demo sleep detection")

# Determine overall hardware availability
HARDWARE_AVAILABLE = GPIO_AVAILABLE and OLED_AVAILABLE and VIBRATION_AVAILABLE

if HARDWARE_AVAILABLE:
    print("✅ Core hardware modules loaded successfully!")
else:
    print("⚠️  Some core modules missing - limited functionality available")
    print("📋 Available modules:")
    if GPIO_AVAILABLE: print("  ✅ GPIO")
    if OLED_AVAILABLE: print("  ✅ OLED")  
    if VIBRATION_AVAILABLE: print("  ✅ Vibration")
    if PROCESSING_AVAILABLE: print("  ✅ Signal Processing")
    if XGBOOST_AVAILABLE: print("  ✅ XGBoost")

class NeuroRiseSystem:
    """Main NeuroRise Smart Alarm System"""
    
    def __init__(self):
        """Initialize the complete NeuroRise system"""
        print("🧠 NeuroRise Smart Alarm System - Initializing...")
        print("="*50)
        
        # System state
        self.running = True
        self.alarm_mode = 'SETUP'  # SETUP, MONITORING, TRIGGERED, STOPPED
        self.sleep_monitoring_active = False
        
        # Initialize available components
        self.oled_system = None
        self.vibration_controller = None
        self.sleep_model = None
        
        # Initialize OLED if available
        if OLED_AVAILABLE:
            try:
                self.oled_system = OLEDTimeSetter()
                print("📱 OLED Display initialized")
            except Exception as e:
                print(f"❌ OLED initialization error: {e}")
        
        # Initialize vibration controller if available
        if VIBRATION_AVAILABLE:
            try:
                self.vibration_controller = VibrationController()
                print("📳 Vibration controller initialized")
            except Exception as e:
                print(f"❌ Vibration initialization error: {e}")
        
        # Load sleep stage model if XGBoost is available
        if XGBOOST_AVAILABLE:
            try:
                model_path = BASE_DIR / 'models' / 'xgb_model.json'
                if model_path.exists():
                    self.sleep_model = XGBClassifier()
                    self.sleep_model.load_model(str(model_path))
                    print("🧠 Sleep stage model loaded")
                else:
                    print("⚠️  Sleep stage model not found - using demo mode")
            except Exception as e:
                print(f"❌ Model loading error: {e}")
        
        print(f"✅ NeuroRise system initialized with available components!")
        print(f"🔧 Hardware available: {HARDWARE_AVAILABLE}")
        print(f"📱 OLED available: {OLED_AVAILABLE}")
        print(f"📳 Vibration available: {VIBRATION_AVAILABLE}")
        print(f"🧠 XGBoost available: {XGBOOST_AVAILABLE}")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum} - shutting down...")
        self.shutdown()
    
    def show_main_menu(self):
        """Display the main system menu"""
        print("\n" + "="*60)
        print("🧠 NeuroRise Smart Alarm System")
        print("="*60)
        print("1. ⏰ Set Alarm Time (OLED + Rotary Encoder)")
        print("2. 🔍 View Current Settings")
        print("3. 🚨 Start Smart Alarm Monitoring")
        print("4. 📳 Test Vibration System")
        print("5. 🔧 Hardware Diagnostics")
        print("6. 🧪 Demo Mode (No EEG Required)")
        print("7. ❌ Exit System")
        print("="*60)
        
        # Show current system status
        if OLED_AVAILABLE:
            time_info = get_set_time_info()
            if time_info['settime_fixed']:
                print(f"📅 Current alarm: {time_info['formatted']}")
                if 'wake_window_minutes' in time_info and time_info['wake_window_fixed']:
                    print(f"⏰ Wake window: {time_info['wake_window_minutes']} minutes before")
            else:
                print("⚠️  No alarm time set")
        else:
            print("⚠️  OLED not available - cannot set/view alarm time")
        print(f"🔄 System mode: {self.alarm_mode}")
        print("="*60)
    
    def set_alarm_time(self):
        """Run the alarm time setting interface"""
        if not OLED_AVAILABLE:
            print("❌ OLED display not available for time setting")
            return
        if not self.oled_system:
            print("❌ OLED system not initialized")
            return
            
        print("\n⏰ Alarm Time Setting")
        print("="*30)
        print("📱 Use OLED display and rotary encoder")
        print("1️⃣ First: Set wake window (0-90 minutes)")
        print("2️⃣ Then: Set wake time (with blinking)")
        print("🔧 Rotate encoder: Adjust values in 5-min steps")
        print("🟢 SET button (pin 23): Confirm window then time")
        print("🔴 RESET button (pin 4): Reset to window selection")
        print("💻 Press Ctrl+C to return to main menu")
        print("="*30)
        
        try:
            self.oled_system.run()
        except KeyboardInterrupt:
            print("\n⏹️  Time setting cancelled")
            self.oled_system.cleanup()
            # Reinitialize for next use
            self.oled_system = OLEDTimeSetter()
    
    def view_settings(self):
        """Display current system settings"""
        print("\n🔍 Current System Settings")
        print("="*35)
        
        if OLED_AVAILABLE:
            time_info = get_set_time_info()
            if time_info['settime_fixed']:
                print(f"⏰ Wake time: {time_info['formatted']}")
                print(f"🕐 24h format: {time_info['hour']:02d}:{time_info['minute']:02d}")
                
                # Show wake window info
                if 'wake_window_minutes' in time_info and time_info['wake_window_fixed']:
                    wake_window = time_info['wake_window_minutes']
                    print(f"⏳ Wake window: {wake_window} minutes before wake time")
                    
                    # Calculate monitoring window using the custom wake window
                    wake_dt = datetime.datetime.fromtimestamp(time_info['settime'])
                    start_time = wake_dt - datetime.timedelta(minutes=wake_window)
                    
                    print(f"🕐 Monitoring starts: {start_time.strftime('%I:%M %p')}")
                    print(f"🕐 Target wake time: {wake_dt.strftime('%I:%M %p')}")
                else:
                    print("⚠️  Wake window not set")
                
                print(f"📊 Sleep model: {'Loaded' if self.sleep_model else 'Demo mode'}")
            else:
                print("⚠️  No alarm time configured")
                print("💡 Use option 1 to set alarm time")
        else:
            print("⚠️  OLED not available - cannot view settings")
        
        print(f"🔧 Component Status:")
        print(f"  📱 OLED: {'Available' if OLED_AVAILABLE else 'Not available'}")
        print(f"  📳 Vibration: {'Available' if VIBRATION_AVAILABLE else 'Not available'}")
        print(f"  🧠 XGBoost: {'Available' if XGBOOST_AVAILABLE else 'Not available'}")
        print(f"  🔌 GPIO: {'Available' if GPIO_AVAILABLE else 'Not available'}")
        print("="*35)
    
    def get_eeg_data(self):
        """
        Collect EEG data from sensor
        TODO: Implement actual EEG data collection
        For now returns simulated data
        """
        # Simulate EEG data - replace with actual sensor reading
        import numpy as np
        fs = 512  # Sample rate
        duration = 30  # 30 seconds of data
        t = np.linspace(0, duration, fs * duration)
        
        # Simulate mixed frequency EEG signal
        eeg_data = (
            0.5 * np.sin(2 * np.pi * 1 * t) +  # Delta
            0.3 * np.sin(2 * np.pi * 6 * t) +  # Theta  
            0.2 * np.sin(2 * np.pi * 10 * t) + # Alpha
            0.1 * np.random.randn(len(t))       # Noise
        )
        
        return eeg_data
    
    def analyze_sleep_stage(self, eeg_data):
        """
        Analyze EEG data to determine sleep stage
        Returns predicted sleep stage
        """
        if not self.sleep_model:
            # Simulate sleep stage detection
            import random
            stages = ['Wake', 'N1', 'N2', 'N3', 'REM']
            return random.choice(stages)
        
        try:
            # Extract features from EEG data
            features = exfeature(eeg_data, fs=512)
            
            # Predict sleep stage
            prediction = self.sleep_model.predict([features])[0]
            return prediction
        except Exception as e:
            print(f"❌ Sleep analysis error: {e}")
            return 'Unknown'
    
    def is_within_wake_window(self, wake_time, window_minutes):
        """Check if current time is within the wake window (before wake time)"""
        now = datetime.datetime.now()
        wake_dt = datetime.datetime.fromtimestamp(wake_time)
        
        # Adjust wake time to today if it's in the past
        if wake_dt.date() < now.date():
            wake_dt = wake_dt.replace(year=now.year, month=now.month, day=now.day)
        
        # Wake window is X minutes BEFORE the wake time
        start_window = wake_dt - datetime.timedelta(minutes=window_minutes)
        end_window = wake_dt  # Window ends at wake time
        
        return start_window <= now <= end_window
    
    def start_smart_alarm(self):
        """Start the smart alarm monitoring system"""
        if not OLED_AVAILABLE:
            print("❌ OLED not available - cannot get alarm settings")
            return
        
        time_info = get_set_time_info()
        if not time_info['settime_fixed']:
            print("❌ No alarm time set! Please set alarm time first.")
            return
        
        if not time_info.get('wake_window_fixed', False):
            print("❌ No wake window set! Please set wake window first.")
            return
        
        wake_window = time_info['wake_window_minutes']
        
        print("\n🚨 Starting Smart Alarm Monitoring")
        print("="*40)
        print(f"⏰ Target wake time: {time_info['formatted']}")
        print(f"⏳ Wake window: {wake_window} minutes before wake time")
        
        # Calculate monitoring window
        wake_dt = datetime.datetime.fromtimestamp(time_info['settime'])
        if wake_dt.date() < datetime.date.today():
            wake_dt = wake_dt.replace(year=datetime.date.today().year, 
                                    month=datetime.date.today().month, 
                                    day=datetime.date.today().day)
        start_time = wake_dt - datetime.timedelta(minutes=wake_window)
        
        print(f"🕐 Monitoring starts: {start_time.strftime('%I:%M %p')}")
        print("🧠 Monitoring sleep stages...")
        print("💤 Waiting for optimal wake window...")
        print("🔴 Press Ctrl+C to stop monitoring")
        print("="*40)
        
        self.alarm_mode = 'MONITORING'
        self.sleep_monitoring_active = True
        alarm_triggered = False
        
        try:
            while self.sleep_monitoring_active and not alarm_triggered:
                # Check if we're in the wake window
                if self.is_within_wake_window(time_info['settime'], wake_window):
                    print(f"🕐 [{datetime.datetime.now().strftime('%H:%M:%S')}] In wake window - analyzing sleep...")
                    
                    # Get EEG data and analyze sleep stage
                    eeg_data = self.get_eeg_data()
                    sleep_stage = self.analyze_sleep_stage(eeg_data)
                    
                    print(f"🧠 Sleep stage detected: {sleep_stage}")
                    
                    # Trigger alarm if in optimal sleep stage (N2)
                    if sleep_stage == 'N2':
                        print("✨ Optimal wake stage detected (N2) - triggering alarm!")
                        self.trigger_smart_alarm()
                        alarm_triggered = True
                        self.alarm_mode = 'TRIGGERED'
                    
                else:
                    # Check if wake time has passed
                    now = datetime.datetime.now()
                    wake_dt = datetime.datetime.fromtimestamp(time_info['settime'])
                    if wake_dt.date() < now.date():
                        wake_dt = wake_dt.replace(year=now.year, month=now.month, day=now.day)
                    
                    if now > wake_dt:
                        print("⏰ Wake time has passed - triggering backup alarm")
                        self.trigger_smart_alarm()
                        alarm_triggered = True
                        self.alarm_mode = 'TRIGGERED'
                    else:
                        print(f"⏳ [{datetime.datetime.now().strftime('%H:%M:%S')}] Waiting for wake window...")
                
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            print("\n⏹️  Smart alarm monitoring stopped by user")
        
        self.sleep_monitoring_active = False
        if not alarm_triggered:
            self.alarm_mode = 'SETUP'
    
    def trigger_smart_alarm(self):
        """Trigger the smart alarm with vibration"""
        print("🚨 SMART ALARM TRIGGERED! 🚨")
        print("📳 Starting vibration alarm...")
        print("🔴 Press RESET button (pin 4) to stop alarm")
        
        try:
            trigger_vibration_alarm(vibrate_duration=1.0, pause_duration=0.2)
            print("✅ Alarm completed - Have a great day! ☀️")
        except Exception as e:
            print(f"❌ Alarm error: {e}")
        finally:
            self.alarm_mode = 'STOPPED'
    
    def test_vibration(self):
        """Test the vibration system"""
        if not VIBRATION_AVAILABLE:
            print("❌ Vibration controller not available for testing")
            return
        if not self.vibration_controller:
            print("❌ Vibration controller not initialized")
            return
            
        print("\n📳 Vibration System Test")
        print("="*25)
        print("1. Single pulse")
        print("2. Alarm pattern") 
        print("3. Custom duration")
        print("4. Back to main menu")
        
        try:
            choice = input("Select test (1-4): ").strip()
            
            if choice == '1':
                print("📳 Single vibration pulse...")
                self.vibration_controller.vibrate_once(duration=1.0)
                print("✅ Pulse completed")
                
            elif choice == '2':
                print("🚨 Testing alarm pattern...")
                print("🔴 Press RESET button (pin 4) to stop")
                trigger_vibration_alarm(vibrate_duration=1.0, pause_duration=0.2)
                
            elif choice == '3':
                duration = float(input("Enter duration (seconds): "))
                print(f"📳 Vibrating for {duration} seconds...")
                self.vibration_controller.vibrate_once(duration=duration)
                print("✅ Test completed")
                
            elif choice == '4':
                return
            else:
                print("❌ Invalid choice")
                
        except ValueError:
            print("❌ Invalid input")
        except Exception as e:
            print(f"❌ Vibration test error: {e}")
    
    def hardware_diagnostics(self):
        """Run comprehensive hardware diagnostics"""
        print("\n🔧 Hardware Diagnostics")
        print("="*25)
        
        # Test OLED
        print("📱 Testing OLED display...")
        if OLED_AVAILABLE and self.oled_system:
            try:
                self.oled_system.update_display()
                print("✅ OLED: Working")
            except Exception as e:
                print(f"❌ OLED: Error - {e}")
        else:
            print("❌ OLED: Not available")
        
        # Test vibration
        print("📳 Testing vibration motor...")
        if VIBRATION_AVAILABLE and self.vibration_controller:
            try:
                self.vibration_controller.vibrate_once(duration=0.5)
                print("✅ Vibration: Working")
            except Exception as e:
                print(f"❌ Vibration: Error - {e}")
        else:
            print("❌ Vibration: Not available")
        
        # Test buttons
        print("🔴 Testing buttons (5 second test)...")
        if GPIO_AVAILABLE:
            try:
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Reset
                GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Set
                
                print("Press RESET (pin 4) and SET (pin 23) buttons...")
                start_time = time.time()
                reset_presses = 0
                set_presses = 0
                last_reset = GPIO.input(4)
                last_set = GPIO.input(23)
                
                while time.time() - start_time < 5:
                    # Check reset button
                    current_reset = GPIO.input(4)
                    if last_reset == 1 and current_reset == 0:
                        reset_presses += 1
                        print(f"🔴 RESET pressed! (count: {reset_presses})")
                    last_reset = current_reset
                    
                    # Check set button
                    current_set = GPIO.input(23)
                    if last_set == 1 and current_set == 0:
                        set_presses += 1
                        print(f"🟢 SET pressed! (count: {set_presses})")
                    last_set = current_set
                    
                    time.sleep(0.05)
                
                print(f"✅ Buttons: RESET({reset_presses}) SET({set_presses})")
                GPIO.cleanup()
                
            except Exception as e:
                print(f"❌ Button test error: {e}")
        else:
            print("❌ GPIO not available for button testing")
        
        # Test model
        print("🧠 Testing sleep stage model...")
        if self.sleep_model:
            print("✅ Model: Loaded")
        else:
            print("⚠️  Model: Not available")
        
        print("🔧 Diagnostics completed!")
    
    def demo_mode(self):
        """Run demo mode without EEG requirements"""
        print("\n🧪 Demo Mode - Smart Alarm Simulation")
        print("="*40)
        print("This mode simulates the smart alarm without EEG input")
        print("1. Quick demo (30 seconds)")
        print("2. Full demo (5 minutes)")
        print("3. Back to main menu")
        
        try:
            choice = input("Select demo (1-3): ").strip()
            
            if choice == '1':
                self.run_quick_demo()
            elif choice == '2':
                self.run_full_demo()
            elif choice == '3':
                return
            else:
                print("❌ Invalid choice")
                
        except Exception as e:
            print(f"❌ Demo error: {e}")
    
    def run_quick_demo(self):
        """Run a quick 30-second demo"""
        print("\n🚀 Quick Demo Starting...")
        stages = ['Wake', 'N1', 'N2', 'N3', 'REM']
        
        for i in range(6):
            stage = stages[i % len(stages)]
            print(f"🧠 [{i*5:2d}s] Sleep stage: {stage}")
            
            if stage == 'N2':
                print("✨ Optimal stage detected - would trigger alarm!")
                if HARDWARE_AVAILABLE:
                    print("📳 Demo vibration...")
                    self.vibration_controller.vibrate_once(duration=0.5)
                break
            
            time.sleep(5)
        
        print("✅ Quick demo completed!")
    
    def run_full_demo(self):
        """Run a full 5-minute demo"""
        print("\n🚀 Full Demo Starting...")
        print("🔴 Press Ctrl+C to stop demo")
        
        try:
            for minute in range(5):
                for second in range(0, 60, 10):
                    elapsed = minute * 60 + second
                    stage = ['Wake', 'N1', 'N2', 'N3', 'REM'][elapsed % 5]
                    
                    print(f"🧠 [{elapsed:3d}s] Sleep stage: {stage}")
                    
                    if stage == 'N2' and elapsed > 120:  # After 2 minutes
                        print("✨ Optimal wake stage detected!")
                        if HARDWARE_AVAILABLE:
                            print("📳 Triggering demo alarm...")
                            trigger_vibration_alarm(vibrate_duration=0.5, pause_duration=0.1)
                        return
                    
                    time.sleep(10)
                    
        except KeyboardInterrupt:
            print("\n⏹️  Full demo stopped")
        
        print("✅ Full demo completed!")
    
    def run(self):
        """Main system loop"""
        print("🧠 NeuroRise Smart Alarm System Ready!")
        
        while self.running:
            try:
                self.show_main_menu()
                choice = input("\nSelect option (1-7): ").strip()
                
                if choice == '1':
                    self.set_alarm_time()
                elif choice == '2':
                    self.view_settings()
                elif choice == '3':
                    self.start_smart_alarm()
                elif choice == '4':
                    self.test_vibration()
                elif choice == '5':
                    self.hardware_diagnostics()
                elif choice == '6':
                    self.demo_mode()
                elif choice == '7':
                    print("👋 Shutting down NeuroRise system...")
                    self.shutdown()
                else:
                    print("❌ Invalid choice, please select 1-7")
                    
            except KeyboardInterrupt:
                print("\n\n👋 System interrupted by user")
                self.shutdown()
            except Exception as e:
                print(f"❌ System error: {e}")
                print("🔄 Continuing operation...")
    
    def shutdown(self):
        """Gracefully shutdown the system"""
        print("🛑 Shutting down NeuroRise system...")
        
        # Stop monitoring
        self.sleep_monitoring_active = False
        self.running = False
        
        # Cleanup hardware
        try:
            if hasattr(self, 'oled_system') and self.oled_system:
                self.oled_system.cleanup()
                print("📱 OLED cleaned up")
            if hasattr(self, 'vibration_controller') and self.vibration_controller:
                self.vibration_controller.cleanup()
                print("📳 Vibration controller cleaned up")
            if GPIO_AVAILABLE:
                GPIO.cleanup()
                print("🔌 GPIO cleaned up")
            print("🧹 Hardware cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
        
        print("✅ NeuroRise system shutdown complete")
        print("💤 Sweet dreams! 🌙")

def main():
    """Main entry point"""
    print("🧠 NeuroRise Smart Alarm System")
    print("="*50)
    print("Intelligent sleep monitoring and wake optimization")
    print("="*50)
    
    # Initialize and run the system
    system = NeuroRiseSystem()
    system.run()

if __name__ == "__main__":
    main()