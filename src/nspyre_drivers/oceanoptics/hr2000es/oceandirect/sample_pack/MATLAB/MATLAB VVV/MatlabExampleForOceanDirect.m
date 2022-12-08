%{
Matlab example for OceanDirect
This example has the same functions as the OceanDirectCSharpExamplecs.cs file
with slight syntactical changes
There are several minor differences with how the functions are called
and what they return.

1. The reference variables (ref) passed as input parameters in C#, and
possibly modified when the function is called, don't "work". The input value must be
included, but Matlab doesn't modified it. Instead, another variable is created
and output. The errorCode value included in the function passed in Matlab
are replaced in the following code by an additional output variable -
errorCodeOut is used here.
2. Many of the variables are return as System types and have to be cast
back to the base type to be used. See line 44. The variable must be cast to
the base type.

%}

clc % Clears cmd window
clear % Clear variables
errorCode = 0; % We need this as a dummy variable input to functions
errorCodeOut = 0; % We need this as the output variable

asm = NET.addAssembly('C:\Program Files\Ocean Insight\OceanDirect SDK\lib\NetOceanDirect.dll'); % Access the .NET dll. Change if it NOT in the default directory
ocean = NetOceanDirect.OceanDirect.getInstance(); % Creates an object to call functions on
devices = ocean.findDevices(); % Finds all attached Ocean spectrometers
if(devices.Length == 0)
    disp('Nothing attached');
    return;
end
 % We need this variable to call functions
deviceId = devices(1).Id; % The default Id is 2
disp(['Device Id = ', num2str(devices(1).Id) ]);
if( deviceId == 0 ) 
    return;
end

errorCodeOut = ocean.openDevice(deviceId, errorCode); % Note left-hand sided variable
if (~errorCodeOut == 0)
    disp(['Failed to open device: ',num2str(deviceId),',', 'errorCode ', num2str(errorCodeOut)]);
else
    disp(['Device Opened with ID: ',num2str(deviceId)]);
    
    deviceName = char(devices(1).Name); % This is a property of the spectrometer
    
    [serialNumber, errorCodeOut] = ocean.getSerialNumber(deviceId, errorCode);
    disp(['Device serial number: ',char(serialNumber)]);
    
    [numberOfPixels, errorCodeOut] = ocean.getNumberOfPixels(deviceId, errorCode);
    disp(['The number of pixels = ',num2str(numberOfPixels)]);
    
    % Get Spectrum and Wavelengths --------------------
    [wavelengths, errorCodeOut] = ocean.getWavelengths(deviceId, errorCode);
    disp(['The first wavelength  = ',num2str(wavelengths(1)),'nm.']);

    [spectrum, errorCodeOut]  = ocean.getSpectrum(deviceId, errorCode);
     disp(['The first spectral value = ',num2str(spectrum(1)),' counts.']);
    plot(wavelengths,spectrum);
end    