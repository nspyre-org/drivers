#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include "api/OceanDirectAPI.h"

int main(int argc, char* argv[]) {
    // Call initialize before using OceanDirect
    odapi_initialize();
    // Probe for Ocean devices
    int foundDevices = odapi_probe_devices();

    if (foundDevices > 0) {
        // Start by getting the devies identifiers we will use in most function calls
        long* ids = malloc(foundDevices * sizeof(long));
        int idCount = odapi_get_device_ids(ids, (unsigned int)foundDevices);

        // Open the first device detected
        int error = 0;
        odapi_open_device(ids[0], &error);

        // Get the serial number
        unsigned char serialMaxLength = odapi_get_serial_number_maximum_length(ids[0], &error);
        char *serial = malloc(serialMaxLength);
        int serialLength = odapi_get_serial_number(ids[0], &error, serial, serialMaxLength);
        printf("Found spectrometer %s\n", serial);

        // Set the integration time to 100ms (100000 microsecs) and acquire a spectrum
        int spectrumLength = odapi_get_formatted_spectrum_length(ids[0], &error);
        double* spectrum = malloc(spectrumLength * sizeof(double));
        unsigned long integrationTime = 100000;
        odapi_set_integration_time_micros(ids[0], &error, integrationTime);
        int acquired = odapi_get_formatted_spectrum(ids[0], &error, spectrum, spectrumLength);

        // For example, find the maximum pixel intensity in the acquired spectrum
        double maxPixelIntensity = 0.0;
        int maxPixel = 0;
        for (int pixel = 0; pixel < spectrumLength; ++pixel) {
            if (spectrum[pixel] > maxPixelIntensity) {
                maxPixelIntensity = spectrum[pixel];
                maxPixel = pixel;
            }
        }
        printf("Maximum pixel is %d, withintensity %f\n", maxPixel, maxPixelIntensity);

        // Clean up by closing the device and calling the shutdown function to free resources in OceanDirect
        odapi_close_device(ids[0], &error);
        odapi_shutdown();

        // Lastly release the allocated memory
        free(ids);
        free(serial);
        free(spectrum);
    }
    else {
        printf("No spectrometers detected\n");
    }
}