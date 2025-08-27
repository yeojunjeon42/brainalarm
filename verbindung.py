import serial
import time

def parse_tgam_packet(packet):
    """
    Parses a TGAM data packet and extracts relevant information.
    """
    # Note: This is a simplified parser based on the provided PDF.
    # You may need to adjust it for full functionality.

    if len(packet) >= 4 and packet[0] == 0xAA and packet[1] == 0xAA:
        payload_len = packet[2]
        if len(packet) >= payload_len + 4:
            payload = packet[3:3+payload_len]
            checksum = packet[3+payload_len]

            # Basic checksum validation (sum of payload bytes, then 1's complement)
            calculated_checksum = (~sum(payload)) & 0xFF

            if calculated_checksum == checksum:
                # Packet is valid, proceed with parsing
                i = 0
                while i < len(payload):
                    code = payload[i]
                    i += 1
                    if code == 0x02: # Poor Signal
                        poor_signal = payload[i]
                        i += 1
                        print(f"Poor Signal: {poor_signal}")
                    elif code == 0x04: # Attention
                        attention = payload[i]
                        i += 1
                        print(f"Attention: {attention}")
                    elif code == 0x05: # Meditation
                        meditation = payload[i]
                        i += 1
                        print(f"Meditation: {meditation}")
                    elif code == 0x80: # Raw Wave Value
                        if i + 1 < len(payload):
                            raw_high = payload[i]
                            raw_low = payload[i+1]
                            raw_wave = (raw_high << 8) | raw_low
                            if raw_wave >= 32768:
                                raw_wave -= 65536
                            i += 2
                            print(f"Raw Wave: {raw_wave}")
                    elif code == 0x83: # EEG Power
                        # Further parsing needed for EEG bands based on the PDF
                        i += 25 # Skip over the detailed EEG data for this example
            else:
                print("Checksum error")

if __name__ == "__main__":
    try:
        # The baud rate for the TGAM module is 57600
        ser = serial.Serial('/dev/rfcomm0', 57600)
        print("Connected to TGAM module...")

        packet_buffer = []
        while True:
            byte = ser.read(1)
            if byte:
                packet_buffer.append(int.from_bytes(byte, 'big'))

                # Look for the start of a packet
                if len(packet_buffer) >= 2 and packet_buffer[-2] == 0xAA and packet_buffer[-1] == 0xAA:
                    if len(packet_buffer) > 2:
                         # Process the previous packet
                        parse_tgam_packet(packet_buffer[:-2])
                    packet_buffer = [0xAA, 0xAA] # Start a new packet

    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()