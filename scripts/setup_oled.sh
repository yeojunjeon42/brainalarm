#!/bin/bash
# OLED Display Setup Script for Raspberry Pi
# This script installs dependencies and enables I2C

echo "Setting up OLED display for Raspberry Pi..."

# Update package list
echo "Updating package list..."
sudo apt update

# Install Python3 and pip if not already installed
echo "Installing Python3 and pip..."
sudo apt install -y python3 python3-pip

# Install required Python packages
echo "Installing Python packages..."
pip3 install adafruit-circuitpython-ssd1306 pillow adafruit-blinka

# Enable I2C interface
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Add user to i2c group
echo "Adding user to i2c group..."
sudo usermod -a -G i2c $USER

# Install i2c-tools for debugging
echo "Installing I2C tools..."
sudo apt install -y i2c-tools

echo ""
echo "Setup complete!"
echo ""
echo "IMPORTANT: Please reboot your Raspberry Pi for I2C changes to take effect:"
echo "sudo reboot"
echo ""
echo "After reboot, you can:"
echo "1. Test I2C: i2cdetect -y 1"
echo "2. Run OLED test: python3 OLED.py"
echo ""
echo "Common OLED I2C addresses: 0x3C or 0x3D"