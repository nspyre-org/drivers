"""
Driver for the Ocean Optics spectrometer HR2000+ES
Author: Benjamin Soloway
Date: 09/14/2022

Use spec.features to see cseabreeze features
Information on this is in python-seabreeze.readthedocs.io/en/latest/backend_api.html
Access trigger mode using
spec.features['spectrometer'][0].set_trigger_mode(5)

Based on page 18 of this reference
https://www.oceaninsight.com/globalassets/catalog-blocks-and-images/manuals--instruction-old-logo/electronic-accessories/external-triggering-options_firmware3.0andabove.pdf
It looks like we want to use data value 4 which will turn on external hardware edge trigger mode.
* Note from page 14 that it looks like it takes 900us to put data into FIFO and 1ms to read data from FIFO.

"In the External Hardware Edge Trigger mode, a rising edge detected by the FPGA from the External
Trigger input starts the Integration Cycle specified through the software interface. After the Integration
Cycle completes, the spectrum is retrieved and written to the FIFO in the FPGA followed by a CCD Reset
Cycle. Only one acquisition will be performed for each External Trigger pulse, no matter what the
pulse’s duration is. The Reset Cycle insures that the CCD performance uniform on a scan-to-scan basis.
The time duration for this reset cycle is relative to the Integration Cycle time and will change if the
integration period is changed. So the timing sequence is Trigger, Trigger Delay, Integration Cycle,
Read/Write Cycle, Reset Cycle, and Idle Cycle(s). The Idle Cycle will until the next trigger occurs."

From page 19 of https://www.oceaninsight.com/globalassets/catalog-blocks-and-images/manuals--instruction-old-logo/spectrometer/hr2000-.pdf
Looks like on the 30-pin cable we need to trigger on 10 and ground on 5.
On the 15-pin cable we need to trigger on 4,5, or 8 and connect to ground on 10.

Maybe can also set the trigger mode this way?
https://python-seabreeze.readthedocs.io/en/latest/api.html?highlight=set_trigger_mode#seabreeze.spectrometers.Spectrometer.trigger_mode
"""
# import multiprocessing

import seabreeze.spectrometers as sb
import time
import logging
try:
    from rpyc.utils.classic import obtain
except ModuleNotFoundError:
    def obtain(i):
        return i

logger = logging.getLogger(__name__)

class HR2000ES():
    def __init__(self):
        self.acq_start_time = 0
        self.elapsed_time_sec = 0

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.spec.close()

    def open(self):
        self.spec = sb.Spectrometer.from_serial_number()

    def set_int_time_sec(self, integration_time):
        """
        set the acquisition integration time in seconds
        """
        self.spec.integration_time_micros(integration_time*10**6)

    def get_time_acquiring_sec(self):
        """
        get the time that the spectrometer has spent acquiring
        """
        curr_time = time.time()
        return self.acq_start_time - curr_time

    def get_elapsed_time_sec(self):
        """
        Return time since the last acquisition
        """
        return self.elapsed_time_sec 

    #TODO: make a function to return the time left before acquisition is done. 
    #   This should use a method that gets the integration time from the hardware

    def acquire(self):
        """
        Acquire wavelength data. Record in self.elapsed_time the time it took to acquire the data
        Return the wavelengths, and intensities
        """
        self.acq_start_time = time.time()

        waves = self.spec.wavelengths()
        ints = self.spec.intensities()

        acq_end_time = time.time()
        self.elapsed_time_sec = acq_end_time - self.acq_start_time

        return (waves, ints)

    def acquire_in_process(self, wls, ints):
        """
        Acquire wavelength data. Record in self.elapsed_time the time it took to acquire the data
        I suggest passing wls, ints = [], [] (as
        """
        self.acq_start_time = time.time()

        wls.append(obtain(self.spec.wavelengths()))
        ints.append(obtain(self.spec.intensities()))

        acq_end_time = time.time()
        self.elapsed_time_sec = acq_end_time - self.acq_start_time

    def set_trigger_mode(self, mode):
        # see modes on pg 18 of
        # https://www.oceaninsight.com/globalassets/catalog-blocks-and-images/manuals--instruction-old-logo/electronic-accessories/external-triggering-options_firmware3.0andabove.pdf
        if mode == 0:
            logger.info('Set spectrometer to Normal ("Free Running") Mode')
            self.spec.trigger_mode(mode)
        elif mode == 3:
            logger.info('Set spectrometer to External Hardware Edge Trigger Mode')
            logger.info("An external trigger rising edge will start the acquisition. Only one acquisition will be performed for each External Trigger pulse, no matter what the pulses' duration is.")
            self.spec.trigger_mode(mode)
        else:
            raise ValueError(f"Invalid mode selection OR if 1,2 I don't know what the mode is: {mode}")

    # def _set_trigger_mode(self, mode):
    #   self.spec.trigger_mode(mode)
    #
    # def _set_trigger(self, mode):
    #   p = multiprocessing.Process(target=self._set_trigger_mode, args=(mode,))
    #   p.start()
    #   p.join(10)
    #   if p.is_alive():
    #       print("running... let's kill it...")
    #       p.terminate()
    #       p.join()

        # elif mode == 1:
        #   logger.info('Set spectrometer to Software Trigger Mode')
        #   logger.info('Continuously takes data when the external trigger is set to high. When low it stops taking data and getSpectrum() will remain blocked (i.e., not return) until the signal goes high again.')
        #   self.spec.trigger_mode(mode)
        # elif mode == 2:
        #   logger.info('Set spectrometer to External Hardware Level Trigger Mode')
        #   logger.info('An external trigger rising edge will start the acquisition. The next acquisition will start if the trigger is still high, FIFO is empty, and spectrum request is active.')
        #   self.spec.trigger_mode(mode)
        # elif mode == 3:
        #   logger.info('Set spectrometer to External Synchronization Trigger Mode')
        #   logger.info('Two triggers needed. The first rising edge starts the integration period and the second rising edge stops the integration while starting the next integration.')
        #   logger.info('Thus the integration time is the period between the two external trigger pulses.')
        #   self.spec.trigger_mode(mode)
        # elif mode == 4:
        #   logger.info('Set spectrometer to External Hardware Edge Trigger Mode')
        #   logger.info("An external trigger rising edge will start the acquisition. Only one acquisition will be performed for each External Trigger pulse, no matter what the pulses' duration is.")
        #   raise ValueError(f'Invalid mode selection: {mode}. The API was wrong when I wrote this code...')
        # else:
        #   raise ValueError(f'Invalid mode selection: {mode}')
