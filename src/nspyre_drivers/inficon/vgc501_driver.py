"""Driver for the INFICON VGC501 pressure gauge via USB-B (virtual COM port).

The VGC501 uses a Pfeiffer-style ASCII serial protocol at 115200 baud:
    1. Send command terminated with CR LF  (e.g. ``PR1\\r\\n``)
    2. Gauge responds with ACK (``\\x06\\r\\n``) or NAK (``\\x15\\r\\n``)
    3. Send ENQ (``\\x05``) to retrieve the data
    4. Gauge responds with a comma-separated string (e.g. ``0,+9.8500E-03\\r\\n``)
"""
import logging
import re
import serial
import threading
import time

logger = logging.getLogger(__name__)

_ACK = b'\x06'
_NAK = b'\x15'
_ENQ = b'\x05'


class VGC501:
    """Driver for the INFICON VGC501 gauge via USB-B (virtual COM port).

    Args:
        port: Serial port, e.g. ``'COM13'``.
        gauge: Gauge channel number used in the ``PR`` command (default 1).
    """

    def __init__(self, port: str, gauge: int = 1):
        self.port = port
        self.gauge = gauge
        self.ser = serial.Serial(
            port=port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=2,
        )
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Low-level protocol
    # ------------------------------------------------------------------
    def _query(self, cmd: str) -> str:
        """Send an ASCII command, perform the ACK/ENQ handshake, and return
        the data response as a string.

        Returns an empty string on NAK, timeout, or communication error.
        """
        with self._lock:
            try:
                self.ser.reset_input_buffer()

                # Step 1: send the command
                self.ser.write((cmd + '\r\n').encode('ascii'))

                # Step 2: read ACK / NAK
                ack_line = self.ser.readline()
                if not ack_line or ack_line[0:1] != _ACK:
                    logger.warning(
                        f'VGC501: expected ACK for "{cmd}", got {ack_line!r}'
                    )
                    return ''

                # Step 3: send ENQ to request the data
                self.ser.write(_ENQ)

                # Step 4: read the data line
                data_line = self.ser.readline().decode('ascii', errors='replace').strip()
                return data_line

            except Exception as e:
                logger.warning(f'VGC501 communication error: {e}')
                return ''

    # ------------------------------------------------------------------
    # High-level API
    # ------------------------------------------------------------------
    def read_pressure(self) -> float:
        """Return the pressure reading from the gauge (in the unit
        configured on the controller, typically Torr).

        Sends the ``PRx`` command where *x* is the gauge channel.
        """
        resp = self._query(f'PR{self.gauge}')
        # Response format: "status,value"  e.g. "0,+9.8500E-03"
        match = re.search(r'([+-]?\d+\.?\d*[Ee][+-]?\d+)', resp)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        logger.warning(f'Failed to parse pressure response: {resp!r}')
        return float('nan')

    def get_latest_pressure(self) -> float:
        """Return the most recent pressure reading."""
        return self.read_pressure()

    def close(self):
        """Close the serial port."""
        try:
            self.ser.close()
        except Exception:
            pass
