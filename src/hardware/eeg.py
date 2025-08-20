#!/usr/bin/env python3
"""
EEG Data Reader for ThinkGear Protocol
Reads and displays raw hex data from ThinkGear EEG devices via serial communication.
Based on NeuroSky ThinkGear packet structure.
"""
import os
import sys
import numpy as np
import serial
import time
import sys
from enum import Enum
from collections import deque
from typing import Optional, Callable, Any
from ..processing.feature_extract import exfeature


class ParserState(Enum):
    """Parser states for ThinkGear packet decoding"""
    NULL = 0x00
    SYNC = 0x01              # Waiting for SYNC byte
    SYNC_CHECK = 0x02        # Waiting for second SYNC byte
    PAYLOAD_LENGTH = 0x03    # Waiting for payload length
    PAYLOAD = 0x04           # Waiting for next payload byte
    CHKSUM = 0x05           # Waiting for checksum byte
    WAIT_HIGH = 0x06        # Waiting for high byte (2-byte raw)
    WAIT_LOW = 0x07         # Waiting for low byte (2-byte raw)


class ParserType(Enum):
    """Parser types"""
    PACKETS = 0x01
    RAW_2BYTE = 0x02


# ThinkGear Protocol Constants
SYNC_BYTE = 0xAA
EXCODE_BYTE = 0x55
MAX_PAYLOAD_LENGTH = 169

# Data codes (from ThinkGear protocol)
CODE_RAW_SIGNAL = 0x80
CODE_ATTENTION = 0x04
CODE_MEDITATION = 0x05
CODE_BLINK_STRENGTH = 0x16
CODE_POOR_SIGNAL = 0x02


class ThinkGearParser:
    """
    ThinkGear Stream Parser
    Based on NeuroSky's ThinkGearStreamParser.c implementation
    """
    
    def __init__(self, parser_type: ParserType = ParserType.PACKETS, 
                 data_handler: Optional[Callable] = None):
        self.parser_type = parser_type
        self.state = ParserState.SYNC if parser_type == ParserType.PACKETS else ParserState.WAIT_HIGH
        self.data_handler = data_handler
        
        # Packet parsing variables
        self.payload_length = 0
        self.payload_bytes_received = 0
        self.payload_sum = 0
        self.payload = bytearray(MAX_PAYLOAD_LENGTH + 1)
        self.checksum = 0
        self.last_byte = 0
        
    def parse_byte(self, byte: int) -> int:
        """
        Parse a single byte according to ThinkGear protocol
        
        Args:
            byte: Input byte to parse
            
        Returns:
            int: Return value
                 0 = normal operation
                 1 = packet completed successfully
                -1 = invalid parser
                -2 = checksum failed
                -3 = payload too long
                -4 = standby mode
                -5 = unrecognized state
        """
        return_value = 0
        
        if self.state == ParserState.SYNC:
            # Waiting for first SYNC byte
            if byte == SYNC_BYTE:
                self.state = ParserState.SYNC_CHECK
                
        elif self.state == ParserState.SYNC_CHECK:
            # Waiting for second SYNC byte
            if byte == SYNC_BYTE:
                self.state = ParserState.PAYLOAD_LENGTH
            else:
                self.state = ParserState.SYNC
                
        elif self.state == ParserState.PAYLOAD_LENGTH:
            # Waiting for payload length
            self.payload_length = byte
            if self.payload_length > 170:
                self.state = ParserState.SYNC
                return_value = -3
            elif self.payload_length == 170:
                return_value = -4  # Standby mode
            else:
                self.payload_bytes_received = 0
                self.payload_sum = 0
                self.state = ParserState.PAYLOAD
                
        elif self.state == ParserState.PAYLOAD:
            # Collecting payload bytes
            self.payload[self.payload_bytes_received] = byte
            self.payload_bytes_received += 1
            self.payload_sum = (self.payload_sum + byte) & 0xFF
            
            if self.payload_bytes_received >= self.payload_length:
                self.state = ParserState.CHKSUM
                
        elif self.state == ParserState.CHKSUM:
            # Verify checksum
            self.checksum = byte
            self.state = ParserState.SYNC
            
            expected_checksum = (~self.payload_sum) & 0xFF
            if self.checksum != expected_checksum:
                return_value = -2
            else:
                return_value = 1
                self._parse_packet_payload()
                
        elif self.state == ParserState.WAIT_HIGH:
            # Waiting for high byte of 2-byte raw value
            if (byte & 0xC0) == 0x80:
                self.state = ParserState.WAIT_LOW
                
        elif self.state == ParserState.WAIT_LOW:
            # Waiting for low byte of 2-byte raw value
            if (byte & 0xC0) == 0x40:
                raw_value = (self.last_byte << 8) | byte
                if self.data_handler:
                    self.data_handler(0, CODE_RAW_SIGNAL, 2, raw_value)
                return_value = 1
            self.state = ParserState.WAIT_HIGH
            
        else:
            # Unrecognized state
            self.state = ParserState.SYNC
            return_value = -5
            
        self.last_byte = byte
        return return_value
        
    def _parse_packet_payload(self):
        """Parse the packet payload and extract data values"""
        i = 0
        
        while i < self.payload_length:
            extended_code_level = 0
            
            # Parse extended code bytes
            while i < self.payload_length and self.payload[i] == EXCODE_BYTE:
                extended_code_level += 1
                i += 1
                
            if i >= self.payload_length:
                break
                
            # Parse code
            code = self.payload[i]
            i += 1
            
            # Parse value length
            if code >= 0x80:
                if i >= self.payload_length:
                    break
                num_bytes = self.payload[i]
                i += 1
            else:
                num_bytes = 1
                
            # Extract value
            if i + num_bytes <= self.payload_length:
                value = self.payload[i:i + num_bytes]
                if self.data_handler:
                    self.data_handler(extended_code_level, code, num_bytes, value)
                i += num_bytes
            else:
                break

class EpochFeatureExtractor:
    def __init__(self, fs=512, epoch_duration=30):
        """
        Args:
            fs (int): Sampling frequency (default 512Hz for TGAM)
            epoch_duration (int): Epoch length in seconds (default 30s)
        """
        self.fs = fs
        self.epoch_duration = epoch_duration
        self.buffer_size = fs * epoch_duration
        self.buffer = deque(maxlen=self.buffer_size)  # raw EEG data 저장
        
    def add_sample(self, sample):
        """새로운 raw EEG 샘플 추가"""
        self.buffer.append(sample)
        
        # 버퍼가 가득 차면 특징 추출
        if len(self.buffer) == self.buffer_size:
            data = np.array(self.buffer, dtype=np.float32)
            features = exfeature(data, fs=self.fs)
            
            # 버퍼 초기화 (슬라이딩 윈도우 원한다면 주석 처리)
            self.buffer.clear()
            
            return features
        return None

class EEGReader:
    """EEG Data Reader with hex display functionality"""
    
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 57600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.parser = ThinkGearParser(ParserType.PACKETS, self._handle_data_value)
        self.running = False
        self.feature_extractor = EpochFeatureExtractor(fs=512, epoch_duration=30)
        self.feature = None
        
    def connect(self) -> bool:
        """
        Connect to the serial port
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0
            )
            print(f"Connected to {self.port} at {self.baudrate} baud")
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {self.port}: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from the serial port"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Disconnected from serial port")
            
    def _handle_data_value(self, extended_code_level: int, code: int, 
                          num_bytes: int, value: Any):
        """Handle parsed data values from ThinkGear packets"""
        timestamp = time.strftime("%H:%M:%S")
        
        if code == CODE_POOR_SIGNAL:
            signal_quality = 100 - value[0] if isinstance(value, (bytes, bytearray)) else 100 - value
            print(f"[{timestamp}] Signal Quality: {signal_quality}%")
            
        elif code == CODE_ATTENTION:
            attention = value[0] if isinstance(value, (bytes, bytearray)) else value
            print(f"[{timestamp}] Attention: {attention}")
            
        elif code == CODE_MEDITATION:
            meditation = value[0] if isinstance(value, (bytes, bytearray)) else value
            print(f"[{timestamp}] Meditation: {meditation}")
            
        elif code == CODE_BLINK_STRENGTH:
            blink = value[0] if isinstance(value, (bytes, bytearray)) else value
            print(f"[{timestamp}] Blink Strength: {blink}")

            
        elif code == CODE_RAW_SIGNAL:
            if isinstance(value, (bytes, bytearray)) and len(value) >= 2:
                raw_val = (value[0] << 8) | value[1]
            else:
                raw_val = value
            print(f"[{timestamp}] Raw Signal: {raw_val}")
            self.feature = self.feature_extractor.add_sample(raw_val)
            
            
        else:
            value_hex = ' '.join([f'{b:02X}' for b in value]) if isinstance(value, (bytes, bytearray)) else f'{value:02X}'
            print(f"[{timestamp}] Code 0x{code:02X} (Level {extended_code_level}): {value_hex}")

    def display_raw_hex(self, buffer_size: int = 32):
        """
        Display raw hex data from serial stream
        
        Args:
            buffer_size: Number of bytes to read at once
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Serial connection not established")
            return
            
        print(f"Displaying raw hex data from {self.port}")
        print("Press Ctrl+C to stop\n")
        
        self.running = True
        byte_count = 0
        
        try:
            while self.running:
                if self.serial_conn.in_waiting > 0:
                    # Read available bytes
                    data = self.serial_conn.read(min(buffer_size, self.serial_conn.in_waiting))
                    
                    if data:
                        timestamp = time.strftime("%H:%M:%S.%f")[:-3]
                        hex_data = ' '.join([f'{b:02X}' for b in data])
                        
                        # Display raw hex
                        print(f"[{timestamp}] RAW HEX: {hex_data}")
                        
                        # Parse each byte through ThinkGear parser
                        for byte_val in data:
                            result = self.parser.parse_byte(byte_val)
                            if result == 1:
                                print(f"[{timestamp}] ✓ Packet parsed successfully")
                            elif result < 0:
                                error_msg = {
                                    -1: "Invalid parser",
                                    -2: "Checksum failed", 
                                    -3: "Payload too long",
                                    -4: "Standby mode",
                                    -5: "Unrecognized state"
                                }.get(result, f"Unknown error {result}")
                                print(f"[{timestamp}] ✗ Parser error: {error_msg}")
                        
                        byte_count += len(data)
                        print(f"Total bytes received: {byte_count}\n")
                        
                else:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
                    
        except KeyboardInterrupt:
            print("\nStopping hex display...")
            self.running = False
    
    def start_monitoring(self):
        """Start monitoring EEG data with parsed output"""
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Serial connection not established")
            return
            
        print(f"Starting EEG monitoring on {self.port}")
        print("Press Ctrl+C to stop\n")
        
        self.running = True
        
        try:
            while self.running:
                if self.serial_conn.in_waiting > 0:
                    byte_val = self.serial_conn.read(1)[0]
                    self.parser.parse_byte(byte_val)
                else:
                    time.sleep(0.001)
                    
        except KeyboardInterrupt:
            print("\nStopping EEG monitoring...")
            self.running = False


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='EEG Data Reader for ThinkGear Protocol')
    parser.add_argument('--port', '-p', default='/dev/serial0', 
                       help='Serial port (default: /dev/serial0)')
    parser.add_argument('--baudrate', '-b', type=int, default=57600,
                       help='Baud rate (default: 57600)')
    parser.add_argument('--mode', '-m', choices=['hex', 'monitor'], default='hex',
                       help='Operation mode: hex (raw hex display) or monitor (parsed data)')
    
    args = parser.parse_args()
    
    # Create EEG reader
    eeg_reader = EEGReader(port=args.port, baudrate=args.baudrate)
    
    # Connect to serial port
    if not eeg_reader.connect():
        sys.exit(1)
    
    try:
        if args.mode == 'hex':
            eeg_reader.display_raw_hex()
        else:
            eeg_reader.start_monitoring()
    finally:
        eeg_reader.disconnect()


if __name__ == "__main__":
    main()
