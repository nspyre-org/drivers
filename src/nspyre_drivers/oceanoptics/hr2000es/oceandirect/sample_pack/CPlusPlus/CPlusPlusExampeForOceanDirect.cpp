#include "api/OceanDirectAPI.h"
#include <iostream>
#include <vector>
#include <memory>

int main() {
    std::cout << "OceanDirect SDK C++ Sample Program" << std::endl;

    // Start by initializing the SDK
    odapi_initialize();
    // Find any connected spectrometers
    int deviceCount = odapi_probe_devices();
    if (deviceCount < 1) {
        std::cout << "No connected spectrometers found" << std::endl;
    }
    else {
        // Retrieve the number of device IDs from the connected spectrometers.
        // The device ID will be used to address a specific spectrometer in later function calls
        int deviceIdCount = odapi_get_number_of_device_ids();
        // Declare a vector to hold the device IDs
        std::vector<long> deviceIds(deviceIdCount);
        // then get the device IDs
        int retrievedIdCount = odapi_get_device_ids(deviceIds.data(), deviceIdCount);
        // Errors in the following functions will be reported in an integer argument, zero indicates success
        int error = 0;
        // Open the first device found to enable it to be used
        odapi_open_device(deviceIds[0], &error);
        if (error != 0) {
            std::cout << "Failed to open the spectrometer. The error code is: " << error << std::endl;
        }
        else {
            // Get the device name
            const int nameLength = 32;
            char deviceName[nameLength] = { 0 };
            odapi_get_device_name(deviceIds[0], &error, deviceName, nameLength);
            if (error != 0) {
                std::cout << "Failed to retrieve the spectrometer type. The error code is: " << error << std::endl;
            }
            // and serial number
            int serialNumberLength = odapi_get_serial_number_maximum_length(deviceIds[0], &error);
            std::unique_ptr<char> serialNumber(new char[serialNumberLength]);
            odapi_get_serial_number(deviceIds[0], &error, serialNumber.get(), serialNumberLength);
            if (error != 0) {
                std::cout << "Failed to retrieve the spectrometer serial number. The error code is: " << error << std::endl;
            }
            else {
                std::cout << "The device is " << deviceName << ", serial number " << serialNumber.get() << std::endl;
            }

            // Find the number of pixels returned by the first spectrometer
            int pixelCount = odapi_get_formatted_spectrum_length(deviceIds[0], &error);
            if (error != 0) {
                std::cout << "Failed to get the spectrum length. The error code is: " << error << std::endl;
            }
            else {
                // and then declare vectors to be used to retrieve the wavelengths and intensities
                std::vector<double> wavelengths(pixelCount);
                std::vector<double> spectrum(pixelCount);
                // get the wavelengths
                int wavelengthCount = odapi_get_wavelengths(deviceIds[0], &error, wavelengths.data(), pixelCount);
                if (error != 0) {
                    std::cout << "Failed to retrieve the wavelengths. Error code is: " << error << std::endl;
                }

                // Now set the integration time to 200ms. The time must be specified in microseconds.
                unsigned long integrationTimeMicroseconds = 200000;
                odapi_set_integration_time_micros(deviceIds[0], &error, integrationTimeMicroseconds);
                if (error != 0) {
                    std::cout << "Failed to set the integration time. Error code is: " << error << std::endl;
                }
                int intensityCount = odapi_get_formatted_spectrum(deviceIds[0], &error, spectrum.data(), pixelCount);
                if (error != 0) {
                    std::cout << "Failed to retrieve the spectrum. Error code is: " << error << std::endl;
                }
                std::cout << "Pixel 0 wavelength is " << wavelengths[0] << std::endl;
                std::cout << "Pixel 0 intensity is " << spectrum[0] << " counts" << std::endl;
            }
            odapi_close_device(deviceIds[0], &error);
        }
    }
    // Finally clean up resources claimed by the SDK
    odapi_shutdown();
}