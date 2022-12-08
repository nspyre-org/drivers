using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using NetOceanDirect;
using System.Threading;
using System.Runtime;
using System.IO;


/*
From the code for v1.14

*/

namespace OceanDirectTest
{
    partial class Test
    {        
        static void Main(string[] args)
        {
            //define this here
            int errorCode = 0; // errorCode returns as zero 

            // create object from dll
            var ocean = OceanDirect.getInstance(); // Create an object to call functions on

            Devices[] devices = ocean.findDevices(); // Find all attached Ocean Spectrometers

            if (devices.Length != 0) // If number of devices not equal 0
            {
                Console.WriteLine("Found " + devices.Length + " spectrometers");
            }
            else // No spectrometers found
            {
                Console.WriteLine("Did not find any spectrometers");
                return; // Need to figure out why
            }

            // We need a deviceID to use functions
            int deviceID = devices[0].Id; // For this example, assume only 1 device index = 0;
            Console.WriteLine("DeviceID  = " + deviceID.ToString()); // The default ID is 2.

            // Devices must be open to call other functions
            ocean.openDevice(deviceID, ref errorCode);
            if(errorCode == 0) // If errorCode is still 0, the device was opened
            {
                Console.WriteLine("Device was opened"); 
            }
            else
            {
                Console.WriteLine("Device was not opened");
                return; // Need to figure out why
            }

            // This is a property of the spectrometer
            string deviceName = devices[0].Name;
            Console.WriteLine("The deviceName is " + deviceName);

            // This is how a function of the ocean object is called
            string serialNumber = ocean.getSerialNumber(deviceID, ref errorCode);
            if ((errorCode == 0) && !string.IsNullOrEmpty(serialNumber)) // if errorCode is still 0 and something was returned
            {
                Console.WriteLine("The device serial number is " + serialNumber);
            }
            else
            {
                Console.WriteLine("Could not read the device serial number.");
            }

            int numberOfPixels = ocean.getNumberOfPixels(deviceID, ref errorCode);
            if ((errorCode == 0) && !string.IsNullOrEmpty(numberOfPixels.ToString())) // if errorCode is still 0 and something was returned
            {
                Console.WriteLine("The number of pixels =  " + numberOfPixels.ToString());
            }
            else
            {
                Console.WriteLine("Could not read the number of pixels.");
            }

            double[] allWaveLengths = ocean.getWavelengths(deviceID, ref errorCode);
            if ((errorCode == 0) && !string.IsNullOrEmpty(allWaveLengths.ToString()))
            {
                Console.WriteLine("The 1st wavelength =  " + allWaveLengths[0].ToString() + "nm");
            }
            else
            {
                Console.WriteLine("Could not read the wavelengths.");
            }

            double[] currentSpectrum = ocean.getSpectrum(deviceID, ref errorCode);
            if ((errorCode == 0) && !string.IsNullOrEmpty(currentSpectrum.ToString()))
            {
                Console.WriteLine("The 1st spectra value =  " + currentSpectrum[0].ToString() + " counts");
            }
            else
            {
                Console.WriteLine("Could not read the spectrum.");
            }
        }
    } 
}
