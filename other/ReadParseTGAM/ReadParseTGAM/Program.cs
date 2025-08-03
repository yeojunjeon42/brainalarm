using System;
using System.IO;

namespace ReadParseTGAM
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Testing Parser with streamLog.txt...");
            
            // Create parser instance
            Parser parser = new Parser();
            
            // Read streamLog.txt file
            string filePath = Path.Combine("..", "..", "thinkgear_testapp", "streamLog.txt");
            
            if (!File.Exists(filePath))
            {
                Console.WriteLine($"Error: Could not find streamLog.txt at {filePath}");
                return;
            }
            
            try
            {
                byte[] fileBytes = File.ReadAllBytes(filePath);
                Console.WriteLine($"Read {fileBytes.Length} bytes from streamLog.txt");
                Console.WriteLine("Starting to parse data...\n");
                
                int packetCount = 0;
                int successCount = 0;
                int checksumErrorCount = 0;
                
                // Process each byte through the parser
                foreach (byte b in fileBytes)
                {
                    int result = parser.parseByte(b);
                    
                    switch (result)
                    {
                        case Parser.PST_PACKET_PARSED_SUCCESS:
                            successCount++;
                            packetCount++;
                            break;
                        case Parser.PST_PACKET_CHECKSUM_FAILED:
                            checksumErrorCount++;
                            packetCount++;
                            break;
                        case Parser.PST_NOT_YET_COMPLETE_PACKET:
                            // Continue parsing
                            break;
                    }
                }
                
                Console.WriteLine($"\n=== Parsing Results ===");
                Console.WriteLine($"Total packets processed: {packetCount}");
                Console.WriteLine($"Successful packets: {successCount}");
                Console.WriteLine($"Checksum errors: {checksumErrorCount}");
                Console.WriteLine($"Success rate: {(double)successCount / packetCount * 100:F1}%");
                
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error reading file: {ex.Message}");
            }
            
            Console.WriteLine("\nPress any key to exit...");
            Console.ReadKey();
        }
    }
}
