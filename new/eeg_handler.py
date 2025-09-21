#!/usr/bin/env python3
import serial
import time
import threading
import queue  # Thread-safe queue for communication
from enum import Enum
from typing import Optional, List, Any, Callable
from src.processing.feature_extract import exfeature
import numpy as np

# ThinkGear Protocol Constants (이전 코드와 동일)
SYNC_BYTE = 0xAA
EXCODE_BYTE = 0x55
MAX_PAYLOAD_LENGTH = 169
CODE_POOR_SIGNAL = 0x02
CODE_RAW_SIGNAL = 0x80

# ParserState Enum & ThinkGearParser Class (이전 코드와 동일하므로 생략)
# ... (이전 답변에 있던 ParserState와 ThinkGearParser 클래스 코드가 여기에 들어갑니다)
class ParserState(Enum):
    SYNC = 0x01
    SYNC_CHECK = 0x02
    PAYLOAD_LENGTH = 0x03
    PAYLOAD = 0x04
    CHKSUM = 0x05

class ThinkGearParser:
    def __init__(self, data_handler: Optional[Callable] = None):
        self.state = ParserState.SYNC
        self.data_handler = data_handler
        self.payload_length = 0
        self.payload_bytes_received = 0
        self.payload_sum = 0
        self.payload = bytearray(MAX_PAYLOAD_LENGTH + 1)
        self.checksum = 0

    def parse_byte(self, byte: int) -> int:
        return_value = 0
        if self.state == ParserState.SYNC:
            if byte == SYNC_BYTE: self.state = ParserState.SYNC_CHECK
        elif self.state == ParserState.SYNC_CHECK:
            self.state = ParserState.PAYLOAD_LENGTH if byte == SYNC_BYTE else ParserState.SYNC
        elif self.state == ParserState.PAYLOAD_LENGTH:
            self.payload_length = byte
            if self.payload_length > MAX_PAYLOAD_LENGTH: self.state = ParserState.SYNC; return_value = -1
            else: self.payload_bytes_received = 0; self.payload_sum = 0; self.state = ParserState.PAYLOAD
        elif self.state == ParserState.PAYLOAD:
            self.payload[self.payload_bytes_received] = byte; self.payload_sum += byte; self.payload_bytes_received += 1
            if self.payload_bytes_received >= self.payload_length: self.state = ParserState.CHKSUM
        elif self.state == ParserState.CHKSUM:
            self.checksum = byte; self.state = ParserState.SYNC
            expected_checksum = (~self.payload_sum) & 0xFF
            if self.checksum != expected_checksum: return_value = -2
            else: return_value = 1; self._parse_packet_payload()
        return return_value

    def _parse_packet_payload(self):
        i = 0
        while i < self.payload_length:
            extended_code_level = 0
            while self.payload[i] == EXCODE_BYTE: extended_code_level += 1; i += 1
            code = self.payload[i]; i += 1
            num_bytes = self.payload[i] if code >= 0x80 else 1
            if code >= 0x80: i+=1
            if i + num_bytes <= self.payload_length:
                value = self.payload[i:i + num_bytes]
                if self.data_handler: self.data_handler(code, value)
                i += num_bytes
            else: break


class EEGReader:
    """
    Manages continuous EEG data collection in a separate thread.
    Produces 30-second data epochs and puts them into a queue.
    """
    def __init__(self, model, port: str, baudrate: int = 57600, duration_sec: int = 30):
        self.port = port
        self.baudrate = baudrate
        self.duration_sec = duration_sec
        self.sampling_rate = 512
        self.target_sample_count = self.sampling_rate * self.duration_sec
        self.model = model

        self.serial_conn: Optional[serial.Serial] = None
        self.parser = ThinkGearParser(data_handler=self._handle_data)
        self.thread: Optional[threading.Thread] = None
        self.running = False

        # Data buffers
        self._raw_buffer = []
        self._quality_buffer = []
        
        # Thread-safe queue for results
        self.data_queue = queue.Queue()

    def connect(self) -> bool:
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1.0)
            print(f"Successfully connected to {self.port}.")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to {self.port}: {e}")
            return False

    def disconnect(self):
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Disconnected from serial port.")

    def _handle_data(self, code: int, value: bytearray):
        """Callback function to handle incoming data from the parser."""
        if code == CODE_RAW_SIGNAL and len(value) == 2:
            raw_val = (value[0] << 8) | value[1]
            if raw_val > 32768:
                raw_val -= 65536
            self._raw_buffer.append(raw_val)
        
        elif code == CODE_POOR_SIGNAL and len(value) == 1:
            self._quality_buffer.append(value[0])

    def _data_collection_loop(self):
        """The main loop for the thread, running continuously."""
        print(f"Continuous data collection thread started...")
        
        while self.running:
            try:
                # 1. Read from serial and parse bytes
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    byte = self.serial_conn.read(1)[0]
                    self.parser.parse_byte(byte)
                else:
                    time.sleep(0.001)

                # 2. Check if a 30-second epoch is complete
                if len(self._raw_buffer) >= self.target_sample_count:
                    print(f"--- 30-second epoch collected. Processing... ---")
                    
                    result: Optional[List[int]] = None
                    # Check signal quality
                    if self._quality_buffer and all(q == 0 for q in self._quality_buffer):
                        print("Signal quality was GOOD. Passing data.")
                        result = list(self._raw_buffer)
                    else:
                        print("Signal quality was POOR. Discarding data.")
                        result = None
                    
                    # 3. Put the result into the queue for the main thread
                    self.data_queue.put(result)
                    
                    # 4. Clear buffers to start collecting the next epoch
                    self._raw_buffer.clear()
                    self._quality_buffer.clear()

            except Exception as e:
                print(f"Error in collection loop: {e}")
                self.running = False
        
        print("One Data collection thread finished.")

    def start_collection(self):
        if self.running:
            print("Collection is already in progress.")
            return
        if not self.serial_conn or not self.serial_conn.is_open:
            print("Cannot start. Serial is not connected.")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._data_collection_loop, daemon=True)
        self.thread.start()

    def stop_collection(self):
        if not self.running:
            print("Collection is not running.")
            return
        print("Stopping data collection...")
        self.running = False
        if self.thread: 
            self.thread.join()
        print("Collection stopped.")

    def get_epoch_data(self, block: bool = True, timeout: Optional[float] = None) -> Optional[int]:
        """
        큐에서 30초 분량의 데이터 epoch를 가져와서 모델로 예측을 수행합니다.

        Args:
            block (bool): True이면 데이터가 있을 때까지 기다립니다 (블로킹).
                          False이면 즉시 반환합니다 (논블로킹).
            timeout (float): 블로킹 모드에서 최대로 기다릴 시간 (초).

        Returns:
            데이터 리스트 또는 (데이터가 없거나 타임아웃 시) None.
        """
        try:
            # block과 timeout 옵션을 queue.get()에 직접 전달합니다.
            datas = np.array(self.data_queue.get(block=block, timeout=timeout))
            predicted_stage = self.model.predict(datas.reshape(1,-1))[0]
            return predicted_stage
        except queue.Empty:
            # 큐가 비어있을 때 (논블로킹 모드 또는 타임아웃) 발생하는 예외입니다.
            return None
    def is_running(self) -> bool:
        return self.thread and self.thread.is_alive()
    """모니터링 스레드가 현재 활성 상태인지 확인합니다."""

# --- Example Usage ---
def main():
    PORT_NAME = '/dev/rfcomm0' # 자신의 시리얼 포트에 맞게 수정하세요.
    
    reader = EEGReader(port=PORT_NAME, baudrate=57600)
    
    if not reader.connect():
        return

    try:
        reader.start_collection()
        
        print("\nMain thread started. Non-blocking check for new data.")
        print("To stop, press Ctrl+C\n")
        
        # 메인 스레드는 멈추지 않고 계속 실행됩니다.
        while True: 
            # 1. 다른 중요한 작업을 수행합니다. (예: UI 업데이트, 키보드 입력 감지 등)
            # print("Main thread is doing other work...")

            # 2. 큐에 새로운 데이터가 있는지 논블로킹으로 확인합니다.
            eeg_data = reader.get_epoch_data(block=False) 

            # 3. 데이터가 있을 경우에만 처리합니다.
            if eeg_data:
                print(f"✨ New 30-second epoch received! Samples: {len(eeg_data)}")
                # 이곳에서 데이터를 분석하거나 다른 곳으로 보낼 수 있습니다.
            
            # 메인 루프가 CPU를 100% 사용하지 않도록 잠시 대기합니다.
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Shutting down.")
    finally:
        reader.stop_collection()
        reader.disconnect()

if __name__ == '__main__':
    main()
