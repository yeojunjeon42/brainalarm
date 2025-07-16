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
    class Program
    {
        

        static void Main(string[] args)
        {
            Parser parser = new Parser();
            COMPortManager manager = new COMPortManager(parser);
            Console.WriteLine("hello!!!!!");

            Thread.Sleep(450000);

            Console.ReadKey();
        }

    }
}
