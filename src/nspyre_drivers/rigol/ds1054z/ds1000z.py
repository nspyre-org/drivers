"""Rigol DS1000Z driver.

Based on  dp832.py
Also based on https://github.com/jtambasco/RigolOscilloscope

Copyright (c) 2023, Jacob Feder & Ben Soloway
All rights reserved.
"""

import time
import logging
import numpy as np

from pyvisa import ResourceManager

_logger = logging.getLogger(__name__)

class _DS1000Z:
    def __init__(self, address):
        """
        Args:
            address: PyVISA resource path.
        """
        self.rm = ResourceManager('@py')
        self.address = address

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()

    def __str__(self):
        return f'DS1000Z {self.address} {self.idn}'

    def open(self):
        try:
            self.device = self.rm.open_resource(self.address)
        except Exception as err:
            raise ConnectionError(f'Failed connecting to DS1000Z @ [{self.address}]') from err
        # 1 second timeout
        self.device.timeout = 5000 #5s
        self.idn = self.device.query('*IDN?').strip()
        _logger.info(f'Connected to DS1000Z [{self}].')
        # see table 1-5
        self.device.write(f'*ESE {1|4|8|16|32}') #not sure what this is...
        self.device.write(f'*SRE {8|32}') #not sure what this is...
        return self

    def close(self):
        self.device.close()

    def _write(self, cmd):
        """Send a VISA command to the device and checks for errors.
        Args:
            cmd: command string to send
        """
        self.device.write(cmd)
        self.device.write('*WAI')
        standard_event_reg = int(self.device.query('*ESR?').strip())
        summary_reg = int(self.device.query('*STB?').strip())
        _logger.debug(f'[{self}] sent command [{cmd}], ESR [{standard_event_reg}],'
            f' STB [{summary_reg}]')
        #questionable_status_reg = int(self.device.query(':STAT:QUES?').strip())
        #_logger.debug(f'[{self}] sent command [{cmd}], ESR [{standard_event_reg}],'
        #    f' STB [{summary_reg}], QSR [{questionable_status_reg}]')
        if standard_event_reg & 32:
            raise RuntimeError(f'DS1000Z [{self}] command [{cmd}] contains a syntax error.')
        if standard_event_reg & 16:
            raise RuntimeError(f'DS1000Z [{self}] command [{cmd}] execution error.')

    def _read_bytes(self, num_bytes):
        self.device.read_bytes(num_bytes)
 
    def _read_raw(self):
        return self.device.read_raw()

    def _ask(self, cmd):
        return self.device.query(cmd)

    def _ask_raw(self, cmd):
        self.device.write(cmd)
        return self._read_raw()
       
class DS1000Z(_DS1000Z):
    '''
    Rigol 1000z driver

    Channels 1 through 4 (or 2 depending on the oscilloscope model) are accessed
    using `[channel_number]`.  e.g. osc[2] for channel 2.  Channel 1 corresponds
    to index 1 (not 0).

    Attributes:
        trigger (`_Rigol1054zTrigger`): Trigger object containing functions
            related to the oscilloscope trigger.
        timebase (`_Rigol1054zTimebase`): Timebase object containing functions
            related to the oscilloscope timebase.
    '''
    def __init__(self, address):
        # If the device is rebooted, the python-usbtmc driver won't work.
        # Somehow, by sending any command using the kernel driver, then
        # python-usbtmc works with this scope.  The following searches
        # the usbtmc numbers and finds the corresponding usb pid, vid
        # and serial, and then issues a command via the kernel driver.
        #rigol_vid = '0x1ab1'
        #rigol_pid = '0x04ce'
        #usb_id_usbtmc = usbtmc_info()
        #for dev in usb_id_usbtmc:
        #    if dev[0] == rigol_vid and dev[1] == rigol_pid:
        #        os.system('echo *IDN? >> /dev/%s' % dev[3])

        _DS1000Z.__init__(self, address)

        self._channels = [_Rigol1054zChannel(c, self) for c in range(1,5)]
        self.trigger = _Rigol1054zTrigger(self)
        self.timebase = _Rigol1054zTimebase(self)

    def __getitem__(self, i):
        assert 1 <= i <= 4, 'Not a valid channel.'
        return self._channels[i-1]

    def __len__(self):
        return len(self._channels)

    def autoscale(self):
        self._write(':aut')

    def clear(self):
        self._write(':clear')

    def run(self):
        self._write(':run')

    def stop(self):
        self._write(':stop')

    def force(self):
        self._write(':tfor')

    def set_single_shot(self):
        self._write(':sing')

    def get_id(self):
        return self._ask('*IDN?')

    def get_averaging(self):
        return self._ask(':acq:aver?')

    def set_averaging(self, count):
        assert count in [2**n for n in range(1, 11)]
        self._write(':acq:aver %i' % count)
        return self.get_averaging()

    def set_averaging_mode(self):
        self._write(':acq:type aver')
        return self.get_mode()

    def set_normal_mode(self):
        self._write(':acq:type norm')
        return self.get_mode()

    def set_high_resolution_mode(self):
        self._write(':acq:type hres')
        return self.get_mode()

    def set_peak_mode(self):
        self._write(':acq:type peak')
        return self.get_mode()

    def get_mode(self):
        modes = {
            'NORM': 'normal',
            'AVER': 'averages',
            'PEAK': 'peak',
            'HRES': 'high_resolution'
        }
        return modes[self._ask(':acq:type?')[:-1]]

    def get_sampling_rate(self):
        return float(self._ask(':acq:srat?'))

    def get_memory_depth(self):
        md = self._ask(':acq:mdep?')
        if md != 'AUTO':
           md = int(md)
        return md

    def set_memory_depth(self, pts):
        num_enabled_chans = sum(self.get_channels_enabled())
        if pts != 'AUTO':
            pts = int(pts)

        if num_enabled_chans == 1:
            assert pts in ('AUTO', 12000, 120000, 1200000, 12000000, 24000000)
        elif num_enabled_chans == 2:
            assert pts in ('AUTO', 6000, 60000, 600000, 6000000, 12000000)
        elif num_enabled_chans in (3, 4):
            assert pts in ('AUTO', 3000, 30000, 300000, 3000000, 6000000)

        self.run()

        r = self._send_cmd(':acq:mdep %s' % pts)

        return r

    def get_channels_enabled(self):
        return [c.enabled() for c in self._channels]

    def selected_channel(self):
        return self._ask(':MEAS:SOUR?')

    def get_screenshot(self, filename, type='png'):
        '''
        Downloads a screenshot from the oscilloscope.

        Args:
            filename (str): The name of the image file.  The appropriate
                extension should be included (i.e. jpg, png, bmp or tif).
            type (str): The format image that should be downloaded.  Options
                are 'jpeg, 'png', 'bmp8', 'bmp24' and 'tiff'.  It appears that
                'jpeg' takes <3sec to download while all the other formats take
                <0.5sec.  Default is 'png'.

        Returns:
            list: Raw datastream containing the image data.
        '''
        #self.file.timeout = 0
        #self._write(':disp:data? on,off,%s' % type)

        assert type in ('jpeg', 'png', 'bmp8', 'bmp24', 'tiff')

        if type == 'jpeg':
            s = 3
        elif type == 'png':
            s = 0.5
        elif type == 'bmp8':
            s = 0.5
        elif type == 'bmp24':
            s = 0.5
        elif type == 'tiff':
            s = 0.5
        time.sleep(s)
        #raw_img = self._read_bytes(3850780)[11:-4]
        raw_img = self._ask_raw(':disp:data? on,off,%s' % type)[11:-4]
        #raw_img = self._read_raw()[11:-4]

        with open(filename, 'wb') as fs:
            fs.write(raw_img)

        return raw_img

class _Rigol1054zChannel:
    def __init__(self, channel, osc):
        self._channel = channel
        self._osc = osc

    def _write(self, cmd):
        cmd = ':chan%i%s' % (self._channel, cmd)
        print(cmd)
        return self._osc._write(cmd)

    def _read(self):
        return self._osc._read()

    def _ask(self, cmd):
        cmd = f":chan{self._channel}{cmd}"
        return self._osc._ask(cmd)

    def get_voltage_rms_V(self):
        return self._osc.ask(':MEAS:ITEM? VRMS,CHAN%i' % self._channel)

    def select_channel(self):
        self._osc.write(':MEAS:SOUR CHAN%i' % self._channel)
        return self._osc.selected_channel()

    def get_coupling(self):
        return self._ask(':coup?')

    def set_coupling(self, coupling):
        coupling = coupling.upper()
        assert coupling in ('AC', 'DC', 'GND')
        self._write(':coup %s' % coupling)
        return self.get_coupling()

    def enable(self):
        self._write(':disp 1' % self._channel)
        return self.enabled()

    def disable(self):
        self._write(':disp 0' % self._channel)
        return self.disabled()

    def enabled(self):
        return bool(int(self._ask(':disp?')))

    def disabled(self):
        return bool(int(self._ask(':disp?'))) ^ 1

    def get_offset_V(self):
        return float(self._ask(':OFFS?'))

    def set_offset_V(self, offset):
        assert -1000 <= offset <= 1000.
        self._write(':OFFS %.4e' % offset)
        return self.get_offset_V()

    def get_range_V(self):
        return self._ask(':rang?')

    def set_range_V(self, range):
        assert 8e-3 <= range <= 800.
        self._write(':rang %.4e' % range)
        return self.get_range_V()

    def set_vertical_scale_V(self, scale):
        assert 1e-3 <= scale <= 100
        self._write(':scal %.4e' % scale)

    def get_vertical_scale_V(self):
        return float(self._ask(':scal?'))

    def get_probe_ratio(self):
        return float(self._ask(':prob?'))

    def set_probe_ratio(self, ratio):
        assert ratio in (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1,\
                         2, 5, 10, 20, 50, 100, 200, 500, 1000)
        self._write(':prob %s' % ratio)
        return self.get_probe_ratio()

    def get_units(self):
        return self._ask(':unit?')

    def set_units(self, unit):
        unit = unit.lower()
        assert unit in ('volt', 'watt', 'amp', 'unkn')
        self._write(':unit %s' % unit)

    def get_data_premable(self):
        '''
        Get information about oscilloscope axes.

        Returns:
            dict: A dictionary containing general oscilloscope axes information.
        '''
        pre = self._osc._ask(':wav:pre?').split(',')
        pre_dict = {
            'format': int(pre[0]),
            'type': int(pre[1]),
            'points': int(pre[2]),
            'count': int(pre[3]),
            'xincrement': float(pre[4]),
            'xorigin': float(pre[5]),
            'xreference': float(pre[6]),
            'yincrement': float(pre[7]),
            'yorigin': float(pre[8]),
            'yreference': float(pre[9]),
        }
        return pre_dict

    def get_data(self, mode='norm', filename=None):
        '''
        Download the captured voltage points from the oscilloscope.

        Args:
            mode (str): 'norm' if only the points on the screen should be
                downloaded, and 'raw' if all the points the ADC has captured
                should be downloaded.  Default is 'norm'.
            filename (None, str): Filename the data should be saved to.  Default
                is `None`; the data is not saved to a file.

        Returns:
            2-tuple: A tuple of two lists.  The first list is the time values
                and the second list is the voltage values.

        '''
        assert mode in ('norm', 'raw')

        # Setup scope
        self._osc._write(':stop')
        self._osc._write(':wav:sour chan%i' % self._channel)
        self._osc._write(':wav:mode %s' % mode)
        self._osc._write(':wav:form byte')

        info = self.get_data_premable()

        max_num_pts = 250000
        num_blocks = info['points'] // max_num_pts
        last_block_pts = info['points'] % max_num_pts

        datas = []
        for i in range(num_blocks+1):
            if i < num_blocks:
                self._osc._write(':wav:star %i' % (1+i*250000))
                self._osc._write(':wav:stop %i' % (250000*(i+1)))
            else:
                if last_block_pts:
                    self._osc._write(':wav:star %i' % (1+num_blocks*250000))
                    self._osc._write(':wav:stop %i' % (num_blocks*250000+last_block_pts))
                else:
                    break
            data = self._osc._ask_raw(':wav:data?')[11:]
            data = np.frombuffer(data, 'B')
            datas.append(data)
        datas = np.concatenate(datas)
        v = (datas - info['yorigin'] - info['yreference']) * info['yincrement']

        t = np.arange(0, info['points']*info['xincrement'], info['xincrement'])
        # info['xorigin'] + info['xreference']

        if filename:
            try:
                os.remove(filename)
            except OSError:
                pass
            np.savetxt(filename, np.c_[t, v], '%.12e', ',')

        return t, v

class _Rigol1054zTrigger:
    def __init__(self, osc):
        self._osc = osc

    def get_trigger_level_V(self):
        return self._osc._ask(':trig:edg:lev?')

    def set_trigger_level_V(self, level):
        self._osc._write(':trig:edg:lev %.3e' % level)
        return self.get_trigger_level_V()

    def get_trigger_holdoff_s(self):
        return self._osc._ask(':trig:hold?')

    def set_trigger_holdoff_s(self, holdoff):
        self._osc._write(':trig:hold %.3e' % holdoff)
        return self.get_trigger_holdoff_s()

    def get_trigger_mode(self):
        return self._osc._ask(':TRIGger:SWEep?')

    def get_trigger_source(self):
        return self._osc._ask(f":TRIGger:EDGe:SOURce?")

    def set_trigger_source(self, chan):
        assert chan in [1,2,3,4]
        self._osc._write(f":TRIGger:EDGe:SOURce CHAN{chan}")
        return self.get_trigger_source()

    """
    def set_trigger_mode(self, mode):
        #assert mode in ["AUTO","NORMal","SINGle", "norm", "singl", "NORM", "SING"] 
        cmd = f':TRIGger:SWEep {mode}'
        #cmd = f':{mode}'
        print(cmd)
        return self._osc._ask(cmd)
    """



class _Rigol1054zTimebase:
    def __init__(self, osc):
        self._osc = osc

    def _write(self, cmd):
        return self._osc._write(':tim%s' % cmd)

    def _ask(self, cmd):
        return self._osc._ask(':tim%s' % cmd)

    def get_timebase_scale_s_div(self):
        return float(self._ask(':scal?'))

    def set_timebase_scale_s_div(self, timebase):
        assert 50e-9 <= timebase <= 50
        self._write(':scal %.4e' % timebase)
        return self.get_timebase_scale_s_div()

    def get_timebase_mode(self):
        return self._ask(':mode?')

    def set_timebase_mode(self, mode):
        mode = mode.lower()
        assert mode in ('main', 'xy', 'roll')
        self._write(':mode %s' % mode)
        return get_timebase_mode()

    def get_timebase_offset_s(self):
        return self._ask(':offs?')

    def set_timebase_offset_s(self, offset):
        self._write(':offs %.4e' % -offset)
        return self.get_timebase_offset_s()



if __name__ == '__main__':

    #Connect to DS1000Z
    ip_addrs = "10.120.98.99"
    visa_address = f'TCPIP::{ip_addrs}::INSTR' #maybe need to use TCPIP0::ip_addrs::INSTR
    with DS1000Z(visa_address) as ds1000z:
        #s1000z.trigger.set_trigger_mode("sing") #"AUTO","NORMal","SINGle",
        print(f"trigger mode: {ds1000z.trigger.get_trigger_mode()}")
        ds1000z.trigger.set_trigger_level_V(1)
        print(f"trigger voltage level: {ds1000z.trigger.get_trigger_level_V()}")
        ds1000z.trigger.set_trigger_source(4) #1-4
        print(f"trigger source: {ds1000z.trigger.get_trigger_source()}")
        ds1000z.timebase.set_timebase_scale_s_div(100e-6) #100us
        print(f"time per div: {ds1000z.timebase.get_timebase_scale_s_div()}")
        ds1000z.timebase.set_timebase_offset_s(0)
        print(f"time offset: {ds1000z.timebase.get_timebase_offset_s()}")
        for i in [1,2,3,4]:
            ds1000z[i].set_vertical_scale_V(2.5) #100us
            print(f"vertical scale: {ds1000z[i].get_vertical_scale_V()}")
            ds1000z[i].set_offset_V(-5)
            print(f"vertical offset: {ds1000z[i].get_offset_V()}")

        ds1000z.run()
        ds1000z.set_single_shot() #when calling this, will trigger on the very first pulse it gets
        time.sleep(1)
        ds1000z.force() #run this so that when getting data there will be data. If already triggered, then this will do nothing
        print(ds1000z[1].get_data()) #one way of getting data. If oscope doesn't trigger then this will error out
        ds1000z.get_screenshot('/home/exodia/Pictures/Screenshots/test.png')
"""
        import matplotlib.pyplot as plt
        for i in [1,2,3,4]:
            xs, ys = ds1000z[i].get_data() #one way of getting data
            plt.plot(xs, ys[:-1], label=f'ch{i}') #for some reason the last data point seems bad
        ds1000z.get_screenshot('/home/ben/Screenshots/test.png')
        plt.legend()
        plt.title('')
        plt.show()
"""