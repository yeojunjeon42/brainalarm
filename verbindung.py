import serial
import time
import statistics

def parse_tgam_packet(packet, raw_data_buffer, attention_value, meditation_value):
    """
    완성된 TGAM 데이터 패킷을 입력받아 분석하고 출력합니다.
    패킷 구조: [SYNC, SYNC, PLENGTH, PAYLOAD..., CHECKSUM]
    """
    # 1. 페이로드 길이, 페이로드, 체크섬 분리
    payload_len = packet[2]
    payload = packet[3 : 3 + payload_len]
    checksum = packet[-1] # 패킷의 마지막 바이트가 체크섬

    # 2. 체크섬 계산 및 검증
    # 페이로드의 모든 바이트를 더한 후, 비트 NOT 연산을 하고 마지막 1바이트만 취함
    calculated_checksum = (~sum(payload)) & 0xFF

    if calculated_checksum == checksum:
        # 체크섬이 유효한 경우, 페이로드 데이터 분석 시작
        i = 0
        while i < len(payload):
            code = payload[i]
            i += 1
            
            if code == 0x02: # Poor Signal (신호 품질)
                if i < len(payload):
                    poor_signal = payload[i]
                    i += 1
                    # 신호 품질이 0이면 가장 좋은 상태입니다.
                    print(f"신호 품질: {poor_signal}")
            
            elif code == 0x04: # Attention (집중도)
                if i < len(payload):
                    attention_value[0] = payload[i]
                    i += 1
            
            elif code == 0x05: # Meditation (명상도)
                if i < len(payload):
                    meditation_value[0] = payload[i]
                    i += 1
            
            elif code == 0x80: # Raw Wave Value (원본 뇌파 데이터)
                if i + 1 < len(payload):
                    raw_high = payload[i]
                    raw_low = payload[i+1]
                    raw_wave = (raw_high << 8) | raw_low
                    if raw_wave >= 32768:
                        raw_wave -= 65536
                    i += 2
                    # 원본 데이터를 버퍼에 저장 (512Hz 샘플링)
                    raw_data_buffer.append(raw_wave)
                    # Raw 신호를 고정 위치에서 실시간 업데이트
                    print(f"\rRaw Wave: {raw_wave}", end="", flush=True)

            elif code == 0x83: # EEG Power (각 뇌파 대역별 세기)
                # 이 값들은 뇌파 분석에 중요하게 사용됩니다.
                if i + 24 <= len(payload):
                    # 8개의 뇌파 밴드(Delta, Theta 등)가 각각 3바이트씩 구성됨
                    # 상세 분석이 필요하면 이 부분을 확장할 수 있습니다.
                    i += 25 # 여기서는 상세 분석 없이 건너뜁니다.
    else:
        # 체크섬이 유효하지 않은 경우 오류 메시지 출력
        print(f"!! 체크섬 오류 !! 계산된 값: {calculated_checksum}, 수신된 값: {checksum}")


if __name__ == "__main__":
    # 시리얼 포트 장치 이름과 보드레이트(통신 속도) 설정
    PORT_NAME = '/dev/rfcomm0'
    BAUD_RATE = 57600
    
    # 데이터 버퍼 및 변수 초기화
    raw_data_buffer = []
    attention_value = [0]  # 리스트로 사용하여 참조 전달
    meditation_value = [0]  # 리스트로 사용하여 참조 전달
    last_mean_time = time.time()
    last_attention_meditation_time = time.time()
    
    ser = None # 시리얼 객체 초기화
    try:
        # 시리얼 포트 연결 (timeout을 1초로 설정하여 무한 대기 방지)
        ser = serial.Serial(PORT_NAME, BAUD_RATE, timeout=1)
        print(f"{PORT_NAME}에 연결되었습니다. 데이터 수신을 시작합니다...")
        print("실시간 데이터 모니터링:")
        print("Raw Wave: --")
        print("Attention: --, Meditation: --", end="", flush=True)
        
        packet_buffer = []
        
        while True:
            # 1. 동기 바이트(0xAA)를 찾을 때까지 한 바이트씩 읽기
            byte = ser.read(1)
            if not byte:
                continue # 타임아웃으로 읽은 데이터가 없으면 계속
            
            # byte를 정수형으로 변환
            current_byte = int.from_bytes(byte, 'big')

            if current_byte == 0xAA:
                packet_buffer.append(current_byte)
                
                # AA가 연속으로 두 번 들어오면 패킷의 시작으로 간주
                if len(packet_buffer) >= 2 and packet_buffer[-1] == 0xAA and packet_buffer[-2] == 0xAA:
                    
                    # 3. 페이로드 길이(PLENGTH) 읽기
                    plength_byte = ser.read(1)
                    if not plength_byte:
                        packet_buffer.clear() # 길이 정보를 못 읽었으면 버퍼 초기화
                        continue
                    
                    plength = int.from_bytes(plength_byte, 'big')
                    
                    # 비정상적인 길이 값 방지 (TGAM 최대 페이로드는 170 미만)
                    if plength > 169:
                        packet_buffer.clear()
                        continue
                        
                    # 4. 페이로드와 체크섬 읽기
                    payload_and_checksum = ser.read(plength + 1)
                    
                    # 5. 모든 데이터가 정상적으로 수신되었는지 확인
                    if len(payload_and_checksum) == plength + 1:
                        # 완성된 전체 패킷 생성: [AA, AA, PLENGTH, PAYLOAD..., CHECKSUM]
                        full_packet = [0xAA, 0xAA, plength] + list(payload_and_checksum)
                        
                        # 패킷 분석 함수 호출
                        parse_tgam_packet(full_packet, raw_data_buffer, attention_value, meditation_value)
                    
                    # 다음 패킷을 위해 버퍼 초기화
                    packet_buffer.clear()
            else:
                # 동기 바이트를 찾는 과정이므로 버퍼를 계속 비워줌
                packet_buffer.clear()
            
            # 1초마다 Attention/Meditation 값 업데이트
            current_time = time.time()
            if current_time - last_attention_meditation_time >= 1.0:
                print(f"\rAttention: {attention_value[0]}, Meditation: {meditation_value[0]}", end="", flush=True)
                last_attention_meditation_time = current_time

    except serial.SerialException as e:
        print(f"시리얼 포트 오류가 발생했습니다: {e}")
        print(f"'{PORT_NAME}' 장치가 존재하는지, rfcomm으로 블루투스가 연결되었는지 확인해주세요.")
        
    except KeyboardInterrupt:
        # 사용자가 Ctrl+C를 눌러 종료할 때
        print("\n프로그램을 종료합니다.")
        
    finally:
        # 프로그램 종료 시 시리얼 포트 연결을 안전하게 닫음
        if ser and ser.is_open:
            ser.close()
            print("시리얼 포트 연결을 닫았습니다.")