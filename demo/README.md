# NeuroRise Smart Alarm - Demo Scripts

This folder contains hardware testing scripts for the NeuroRise smart alarm system.

## Available Demo

### `vibration.py` - **HARDWARE** Vibration Testing
**Purpose**: Test actual vibration hardware and GPIO controls on Raspberry Pi

**Features**:
- 📳 **Real Hardware Testing**: Controls actual vibration motor on pin 27
- 🔴 **Button Testing**: Reads reset button state on pin 4  
- 🚨 **Full Alarm Test**: Complete wake-up sequence with button stop
- 🔧 **Component Testing**: Individual tests for debugging hardware issues
- ⚡ **Safety Features**: Proper GPIO cleanup and error handling

**Hardware Requirements**:
- Raspberry Pi with GPIO pins
- Vibration motor connected to pin 27
- Reset button connected to pin 4 (with pull-up)
- RPi.GPIO Python library

**Usage**:
```bash
python3 demo/vibration.py
```

**Test Options**:
1. 🚨 **Full Smart Alarm**: Complete alarm sequence (press reset button to stop)
2. 📳 **Single Vibration**: Test motor for 2 seconds  
3. 🔴 **Button Test**: Monitor button presses for 10 seconds
4. 🔧 **All Tests**: Run complete hardware validation



## How the Real System Works

### Sleep Monitoring Process:
1. **EEG Data Collection**: Real-time brainwave monitoring via forehead electrodes
2. **Feature Extraction**: Signal processing extracts frequency band powers and sleep spindles
3. **ML Classification**: XGBoost model predicts current sleep stage every 30 seconds
4. **Smart Timing**: System only triggers alarm during N2 (light sleep) within wake window

### Wake-up Process:
1. **Optimal Detection**: N2 stage detected within 30 minutes of target wake time
2. **Gentle Vibration**: 1-second pulses with brief pauses (pin 27)
3. **User Response**: Reset button (pin 4) stops alarm when user responds
4. **Progressive Intensity**: Continues until user response or max cycles reached

### Hardware Components:
- **Raspberry Pi Zero W**: Main processing unit
- **EEG Sensors**: Forehead-mounted electrodes (Muse-style headband)
- **OLED Display (128x64)**: Time setting and status display
- **Rotary Encoder**: Time adjustment (5-minute increments)
- **Push Buttons**: Set time and reset/stop alarm
- **Vibration Motor**: Gentle wake-up alerts


## Running on Different Systems

- ❌ **Mac/Windows/Linux**: Hardware demos require Raspberry Pi GPIO
- ✅ **Raspberry Pi**: Full hardware testing available
- ⚠️ **Dependencies**: Requires RPi.GPIO library and proper hardware connections

## Next Steps

After running hardware tests:
1. Deploy to Raspberry Pi for real hardware testing
2. Connect EEG sensors for actual sleep monitoring
3. Calibrate ML model with personal sleep data
4. Customize wake windows and vibration patterns

---

**Note**: This hardware demo tests actual vibration and button components. For full system testing, connect EEG sensors and run the complete smart alarm from `src/alarm/smart_alarm.py`.