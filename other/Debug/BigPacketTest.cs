using System;
using System.IO;
using System.Globalization;
using ReadParseTGAM;

namespace BigPacketTest
{
    class BigPacketParser : Parser
    {
        public new int parseByte(byte buffer)
        {
            int result = base.parseByte(buffer);
            
            if (result == PST_PACKET_PARSED_SUCCESS)
            {
                // Access payload data through reflection to analyze the packet
                var payloadField = typeof(Parser).GetField("payload", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                var payloadLengthField = typeof(Parser).GetField("payloadLength", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                
                if (payloadField != null && payloadLengthField != null)
                {
                    byte[] payload = (byte[])payloadField.GetValue(this);
                    int payloadLength = (int)payloadLengthField.GetValue(this);
                    
                    if (payloadLength >= 30) // Only analyze big packets
                    {
                        AnalyzeBigPacket(payload, payloadLength);
                    }
                }
            }
            
            return result;
        }
        
        private void AnalyzeBigPacket(byte[] payload, int payloadLength)
        {
            Console.WriteLine("\n" + new string('=', 70));
            Console.WriteLine("🔥 ** BIG PACKET DETECTED - EEG_POWER (32 bytes) **");
            Console.WriteLine(new string('=', 70));
            Console.WriteLine($"📦 Payload Size: {payloadLength} bytes");
            Console.WriteLine($"📄 Raw Hex Data: {BitConverter.ToString(payload, 0, payloadLength)}");
            Console.WriteLine();
            
            Console.WriteLine("🧠 DETAILED EEG FREQUENCY BAND ANALYSIS:");
            Console.WriteLine("Based on NeuroSky ThinkGear Protocol Documentation");
            Console.WriteLine(new string('-', 70));
            
            int i = 0;
            while (i < payloadLength)
            {
                // Skip extended codes
                while (i < payloadLength && payload[i] == 85) // PARSER_EXCODE_BYTE
                {
                    Console.WriteLine($"   ⚡ Extended Code detected at byte {i}");
                    i++;
                }
                
                if (i >= payloadLength) break;
                
                int code = payload[i++] & 0xFF;
                int valueBytesLength = 1;
                
                Console.WriteLine($"   📊 Data Code: {code} (0x{code:X2})");
                
                if (code > 127) // MULTI_BYTE_CODE_THRESHOLD
                {
                    if (i < payloadLength)
                    {
                        valueBytesLength = payload[i++] & 0xFF;
                        Console.WriteLine($"   📏 Multi-byte length: {valueBytesLength} bytes");
                    }
                }
                
                switch (code)
                {
                    case 2: // POOR_SIGNAL
                        if (i < payloadLength)
                        {
                            int signal = payload[i] & 0xFF;
                            Console.WriteLine($"   📶 SIGNAL QUALITY: {signal}");
                            Console.WriteLine($"      └─ 0 = Perfect contact, 200 = No contact");
                        }
                        break;
                        
                    case 4: // ATTENTION (eSense)
                        if (i < payloadLength)
                        {
                            int attention = payload[i] & 0xFF;
                            Console.WriteLine($"   🎯 ATTENTION (eSense): {attention}/100");
                            Console.WriteLine($"      └─ Mental focus and concentration level");
                        }
                        break;
                        
                    case 5: // MEDITATION (eSense)
                        if (i < payloadLength)
                        {
                            int meditation = payload[i] & 0xFF;
                            Console.WriteLine($"   🧘 MEDITATION (eSense): {meditation}/100");
                            Console.WriteLine($"      └─ Mental relaxation and calm state");
                        }
                        break;
                        
                    case 131: // EEG_POWER - The main event!
                        Console.WriteLine($"   🎵 ** EEG POWER SPECTRUM ** ({valueBytesLength} bytes)");
                        Console.WriteLine($"      ╔══════════════════════════════════════════════════╗");
                        Console.WriteLine($"      ║  This contains the 8 EEG frequency band powers   ║");
                        Console.WriteLine($"      ║  Each band uses 3 bytes (24-bit values)         ║");
                        Console.WriteLine($"      ╚══════════════════════════════════════════════════╝");
                        
                        if (valueBytesLength >= 24) // Standard EEG power packet (8 bands × 3 bytes)
                        {
                            string[] bandNames = {
                                "Delta (0.5-2.75Hz)",     // Deep sleep, unconscious
                                "Theta (3.5-6.75Hz)",     // REM sleep, deep meditation  
                                "Low-Alpha (7.5-9.25Hz)", // Relaxed awareness
                                "High-Alpha (10-11.75Hz)", // Relaxed awareness
                                "Low-Beta (13-16.75Hz)",   // Focused attention
                                "High-Beta (18-29.75Hz)",  // Alert, active thinking
                                "Low-Gamma (31-39.75Hz)",  // High cognitive processing
                                "High-Gamma (41-49.75Hz)"  // Peak cognitive processing
                            };
                            
                            Console.WriteLine();
                            for (int band = 0; band < 8 && (i + band * 3 + 2) < payloadLength; band++)
                            {
                                int bandIndex = i + band * 3;
                                
                                // Read 3-byte value (big-endian)
                                int value = (payload[bandIndex] << 16) | 
                                          (payload[bandIndex + 1] << 8) | 
                                          payload[bandIndex + 2];
                                
                                // Create visual bar representation
                                int barLength = Math.Min(value / 50000, 40); // Scale for display
                                string bar = new string('█', Math.Max(0, barLength));
                                
                                Console.WriteLine($"      🌊 {bandNames[band],-22}: {value,8:N0} µV² {bar}");
                            }
                            Console.WriteLine();
                            Console.WriteLine($"      💡 Higher values = More activity in that frequency band");
                        }
                        break;
                        
                    default:
                        Console.WriteLine($"   ❓ Unknown Code {code}: {valueBytesLength} bytes");
                        // Show hex dump of unknown data
                        if (valueBytesLength > 0 && i + valueBytesLength <= payloadLength)
                        {
                            string hexDump = BitConverter.ToString(payload, i, Math.Min(valueBytesLength, 16));
                            Console.WriteLine($"      Data: {hexDump}");
                        }
                        break;
                }
                
                i += valueBytesLength;
            }
            
            Console.WriteLine(new string('=', 70));
        }
    }

    class Program
    {
        static void Main(string[] args)
        {
            string logFile = "thinkgear_testapp/streamLog.txt";
            
            if (!File.Exists(logFile))
            {
                Console.WriteLine($"Error: {logFile} not found!");
                return;
            }

            Console.WriteLine("🧠 NeuroSky ThinkGear BIG PACKET Analysis");
            Console.WriteLine("Focused on 32-byte EEG_POWER packets");
            Console.WriteLine("Reference: https://developer.neurosky.com/docs/doku.php?id=thinkgear_communications_protocol");
            Console.WriteLine();

            BigPacketParser parser = new BigPacketParser();
            int bigPacketsFound = 0;

            try
            {
                using (StreamReader reader = new StreamReader(logFile))
                {
                    string line;
                    int lineNumber = 0;
                    
                    while ((line = reader.ReadLine()) != null)
                    {
                        lineNumber++;
                        
                        if (string.IsNullOrWhiteSpace(line))
                            continue;

                        int colonIndex = line.IndexOf(':');
                        if (colonIndex == -1)
                            continue;

                        string hexData = line.Substring(colonIndex + 1).Trim();
                        if (string.IsNullOrEmpty(hexData))
                            continue;

                        // Only process lines with big packets
                        if (!hexData.Contains("AA AA 20"))
                            continue;
                            
                        Console.WriteLine($"⏱️  Line {lineNumber}: {hexData}");
                        
                        string[] hexBytes = hexData.Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
                        
                        foreach (string hexByte in hexBytes)
                        {
                            if (hexByte.Length == 2)
                            {
                                try
                                {
                                    byte b = byte.Parse(hexByte, NumberStyles.HexNumber);
                                    int result = parser.parseByte(b);
                                    
                                    if (result == Parser.PST_PACKET_PARSED_SUCCESS)
                                    {
                                        bigPacketsFound++;
                                        Console.WriteLine("✅ BIG PACKET PARSED SUCCESSFULLY!\n");
                                    }
                                    else if (result == Parser.PST_PACKET_CHECKSUM_FAILED)
                                    {
                                        Console.WriteLine("❌ Checksum failed on big packet!\n");
                                    }
                                }
                                catch (FormatException)
                                {
                                    // Skip invalid hex
                                }
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error reading file: {ex.Message}");
                return;
            }

            Console.WriteLine($"\n🎉 Analysis Complete! Found and analyzed {bigPacketsFound} big EEG packets.");
            Console.WriteLine("These packets contain the detailed brainwave frequency analysis!");
        }
    }
} 