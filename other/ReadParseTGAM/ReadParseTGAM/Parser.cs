using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace ReadParseTGAM
{
    public class Parser
    {

        public const int PARSER_CODE_POOR_SIGNAL = 2;
        public const int PARSER_CODE_HEARTRATE = 3;
        public const int PARSER_CODE_CONFIGURATION = 4;
        public const int PARSER_CODE_RAW = 128;
        public const int PARSER_CODE_DEBUG_ONE = 132;
        public const int PARSER_CODE_DEBUG_TWO = 133;
        public const int PARSER_CODE_EEG_POWER = 131;

        public const int PST_PACKET_CHECKSUM_FAILED = -2;
        public const int PST_NOT_YET_COMPLETE_PACKET = 0;
        public const int PST_PACKET_PARSED_SUCCESS = 1;
        public const int MESSAGE_READ_RAW_DATA_PACKET = 17;
        public const int MESSAGE_READ_DIGEST_DATA_PACKET = 18;

        private const int RAW_DATA_BYTE_LENGTH = 2;
        private const int EEG_DEBUG_ONE_BYTE_LENGTH = 5;
        private const int EEG_DEBUG_TWO_BYTE_LENGTH = 3;
        private const int PARSER_SYNC_BYTE = 170;
        private const int PARSER_EXCODE_BYTE = 85;
        private const int MULTI_BYTE_CODE_THRESHOLD = 127;
        private const int PARSER_STATE_SYNC = 1;
        private const int PARSER_STATE_SYNC_CHECK = 2;
        private const int PARSER_STATE_PAYLOAD_LENGTH = 3;
        private const int PARSER_STATE_PAYLOAD = 4;
        private const int PARSER_STATE_CHKSUM = 5;

        private int parserStatus;
        private int payloadLength;
        private int payloadBytesReceived;
        private int payloadSum;
        private int checksum;
        private byte[] payload = new byte[256];


        public Parser()
        {
            this.parserStatus = PARSER_STATE_SYNC;
        }

        public int parseByte(byte buffer)
        {
            int returnValue = 0;
            switch (this.parserStatus)
            {
                case 1:
                    if ((buffer & 0xFF) != PARSER_SYNC_BYTE) break; this.parserStatus = PARSER_STATE_SYNC_CHECK;
                    break;
                case 2:
                    if ((buffer & 0xFF) == PARSER_SYNC_BYTE)
                        this.parserStatus = PARSER_STATE_PAYLOAD_LENGTH;
                    else
                    {
                        this.parserStatus = PARSER_STATE_SYNC;
                    }
                    break;
                case 3:
                    this.payloadLength = (buffer & 0xFF);
                    this.payloadBytesReceived = 0;
                    this.payloadSum = 0;
                    this.parserStatus = PARSER_STATE_PAYLOAD;
                    break;
                case 4:
                    this.payload[(this.payloadBytesReceived++)] = buffer;
                    this.payloadSum += (buffer & 0xFF);
                    if (this.payloadBytesReceived < this.payloadLength) break; this.parserStatus = PARSER_STATE_CHKSUM;
                    break;
                case 5:
                    this.checksum = (buffer & 0xFF);
                    this.parserStatus = PARSER_STATE_SYNC;
                    if (this.checksum != ((this.payloadSum ^ 0xFFFFFFFF) & 0xFF))
                    {
                        returnValue = -2;
                        Console.WriteLine("CheckSum ERROR!!");
                    }
                    else
                    {
                        returnValue = 1;
                        parsePacketPayload();
                    }
                    break;
            }
            return returnValue;
        }

        private void parsePacketPayload()
        {
            int i = 0;
            int extendedCodeLevel = 0;
            int code = 0;
            int valueBytesLength = 0;

            int signal = 0; int config = 0; int heartrate = 0;
            int rawWaveData = 0;
            while (i < this.payloadLength)
            {
                extendedCodeLevel++;

                while (this.payload[i] == PARSER_EXCODE_BYTE)
                {
                    i++;
                }

                code = this.payload[(i++)] & 0xFF;

                if (code > MULTI_BYTE_CODE_THRESHOLD)
                {
                    valueBytesLength = this.payload[(i++)] & 0xFF;
                }
                else
                {
                    valueBytesLength = 1;
                }

                if (code == PARSER_CODE_RAW)
                {
                    if ((valueBytesLength == RAW_DATA_BYTE_LENGTH))
                    {
                        byte highOrderByte = this.payload[i];
                        byte lowOrderByte = this.payload[(i + 1)];

                        rawWaveData = getRawWaveValue(highOrderByte, lowOrderByte);

                        if (rawWaveData > 32768) rawWaveData -= 65536;

                        Console.WriteLine("Raw:"+rawWaveData);

                    }
                    i += valueBytesLength;
                }
                else
                {
                    switch (code)
                    {
                        case PARSER_CODE_POOR_SIGNAL:
                            signal = this.payload[i] & 0xFF;
                            i += valueBytesLength;
                            Console.Write("PQ:" + signal);
                            break;
                        case PARSER_CODE_EEG_POWER:
                            i += valueBytesLength;
                            break;
                        case PARSER_CODE_CONFIGURATION:
                            if ( signal == 29 || signal == 54 || signal == 55 || signal == 56 || signal == 80 || signal == 81 || signal == 82 || signal == 107 || signal == 200)
                            {
                                config = this.payload[i] & 0xFF;

                                Console.Write("--NoShouldAtt:" + config);

                                Console.WriteLine("");

                                i += valueBytesLength;
                               
                                break; 
                            }
                            else
                            {

                                config = this.payload[i] & 0xFF;

                                Console.Write("--Att:" + config);
                                Console.WriteLine("");

                            }

                            i += valueBytesLength;
                            break;
                        case PARSER_CODE_HEARTRATE:
                            heartrate = this.payload[i] & 0xFF;
                            i += valueBytesLength;

                            break;
                        case PARSER_CODE_DEBUG_ONE:
                            if (valueBytesLength == EEG_DEBUG_ONE_BYTE_LENGTH)
                            {
                                i += valueBytesLength;
                            }
                            break;
                        case PARSER_CODE_DEBUG_TWO:
                            if (valueBytesLength == EEG_DEBUG_TWO_BYTE_LENGTH)
                            {
                                i += valueBytesLength;
                            }
                            break;
                    }
                }
            }
            this.parserStatus = PARSER_STATE_SYNC;
        }

        private int getRawWaveValue(byte highOrderByte, byte lowOrderByte)
        {
            /* Sign-extend the signed high byte to the width of a signed int */
            int hi = (int)highOrderByte;

            /* Extend low to the width of an int, but keep exact bits instead of sign-extending */
            int lo = ((int)lowOrderByte) & 0xFF;

            /* Calculate raw value by appending the exact low bits to the sign-extended high bits */
            int value = (hi << 8) | lo;

            return (value);
        }




    }

}
