using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.IO;
using System.IO.Ports;
using System.Threading;

namespace ReadParseTGAM
{
    class COMPortManager
    {
        Parser parser;
        SerialPort chris_COM;
        Thread readThread;
        bool keepReading;

        public COMPortManager(Parser p) {
            parser = p;

            Console.WriteLine("Input your COM port,like COM3 or COM40,then press Enter key!");

            String strPort = Console.ReadLine();

            Console.WriteLine("Your COM port is:" + strPort);

            chris_COM = new SerialPort();

            chris_COM.BaudRate = 57600;
            chris_COM.PortName = strPort;
            chris_COM.DataBits = 8;
            chris_COM.Open();

            keepReading = true;
            readThread = new Thread(ReadPort);
            readThread.Start();

            //chris_COM.DataReceived += new SerialDataReceivedEventHandler(OnDataReceived);
        }

        private void OnDataReceived(object sender, SerialDataReceivedEventArgs e) {

            Console.WriteLine(sender);
            
        
        }

        private void ReadPort() { 

            while(keepReading){
                if(chris_COM.IsOpen){
                
                    byte[] chris_buffer = new byte[chris_COM.ReadBufferSize + 1];

                    int count = chris_COM.Read(chris_buffer, 0, chris_COM.ReadBufferSize);


                    for (int i = 0; i < count; i++)
                    {
                        parser.parseByte(chris_buffer[i]);
                        //Console.WriteLine("XX:" + i);
                    }

                    //Console.WriteLine(count);
                
                
                }
            
            
            
            
            }
        
        
        }









    }
}
