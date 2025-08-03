# NeuroRise Smart Alarm System

An intelligent EEG-based alarm system that wakes you during optimal sleep phases for better rest quality.

## Features

- **EEG Sleep Stage Detection**: Uses machine learning to identify sleep phases
- **Smart Wake Windows**: Wakes you during light sleep stages within a configurable time window
- **OLED Time Display**: Interactive time setting with rotary encoder and buttons
- **Hardware Integration**: GPIO control for sensors and user interface

## Project Structure

```
Repository/
├── src/                    # Main source code
│   ├── display/           # OLED display controllers
│   ├── alarm/             # Smart alarm logic
│   ├── processing/        # Signal processing and feature extraction
│   └── hardware/          # GPIO and hardware interfaces
├── models/                # Machine learning models
├── data/                  # Data storage (raw, processed, calibration)
├── tests/                 # Test files
├── scripts/               # Setup and utility scripts
├── docs/                  # Documentation
└── other/                 # Legacy/misc files
```

## Quick Start

1. **Hardware Setup**: Run the setup script
   ```bash
   bash scripts/setup_oled.sh
   ```

2. **OLED Time Setter**: Set wake time using rotary encoder
   ```bash
   python src/display/oled_time_setter.py
   ```

3. **Smart Alarm**: Run the intelligent alarm system
   ```bash
   python src/alarm/smart_alarm.py
   ```

## Components

### Display System
- `src/display/oled_time_setter.py` - Interactive time setting interface
- `src/display/simple_time.py` - Basic time display
- `src/display/digital_clock.py` - Continuous clock display
- `src/display/OLED.py` - OLED display utilities

### Smart Alarm
- `src/alarm/smart_alarm.py` - Main smart alarm logic
- Uses XGBoost model to predict sleep stages from EEG features

### Signal Processing
- `src/processing/feature_extract.py` - EEG feature extraction
- `src/processing/signal_processing.py` - Signal processing utilities

### Hardware Interface
- `src/hardware/gpio_time_setter.py` - GPIO-based time setting

## Dependencies

- Python 3.7+
- RPi.GPIO (for Raspberry Pi)
- adafruit-circuitpython-ssd1306
- PIL (Pillow)
- XGBoost
- YASA (sleep analysis)
- NumPy, SciPy

## Hardware Requirements

- Raspberry Pi with GPIO pins
- SSD1306 OLED display (128x64)
- Rotary encoder
- Push buttons
- EEG sensor (for sleep monitoring)

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run hardware setup: `bash scripts/setup_oled.sh`
4. Configure your hardware connections

## Usage

The system operates in two main modes:

1. **Time Setting Mode**: Use the rotary encoder and buttons to set your desired wake time
2. **Smart Alarm Mode**: The system monitors your sleep and wakes you during optimal phases

## License

[Add your license here]