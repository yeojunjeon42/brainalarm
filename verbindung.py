def parse_tgam_packet(packet):
    """
    Parses a TGAM data packet and extracts relevant information.
    """
    if len(packet) >= 4 and packet[0] == 0xAA and packet[1] == 0xAA:
        payload_len = packet[2]
        if len(packet) >= payload_len + 4:
            payload = packet[3:3+payload_len]
            checksum = packet[3+payload_len]
            
            calculated_checksum = (~sum(payload)) & 0xFF
            
            if calculated_checksum == checksum:
                i = 0
                while i < len(payload):
                    code = payload[i]
                    i += 1
                    
                    # 각 값을 읽기 전에 데이터가 더 남아있는지 확인하는 코드를 추가합니다.
                    if code == 0x02: # Poor Signal
                        if i < len(payload): # <<< 안전장치 추가
                            poor_signal = payload[i]
                            i += 1
                            print(f"Poor Signal: {poor_signal}")
                    elif code == 0x04: # Attention
                        if i < len(payload): # <<< 안전장치 추가
                            attention = payload[i]
                            i += 1
                            print(f"Attention: {attention}")
                    elif code == 0x05: # Meditation
                        if i < len(payload): # <<< 안전장치 추가
                            meditation = payload[i]
                            i += 1
                            print(f"Meditation: {meditation}")
                    elif code == 0x80: # Raw Wave Value
                        if i + 1 < len(payload): # <<< 2바이트를 읽으므로 i+1 확인
                            raw_high = payload[i]
                            raw_low = payload[i+1]
                            raw_wave = (raw_high << 8) | raw_low
                            if raw_wave >= 32768:
                                raw_wave -= 65536
                            i += 2
                            print(f"Raw Wave: {raw_wave}")
                    elif code == 0x83: # EEG Power
                        if i + 24 < len(payload): # <<< EEG 데이터 길이(25)만큼 건너뛸 수 있는지 확인
                            i += 25 
            else:
                print("Checksum error")