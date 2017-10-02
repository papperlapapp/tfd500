"""
A python class to control the ELV TFD500 data logger.
"""

# Prepare for python 3
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Standard imports
import datetime
import struct

# Non-standard imports
import serial


class Tfd500(object):
    """
    TFD500 abstraction class.
    """

    def __init__(self, device="/dev/ttyUSB0"):
        self.device      = device
        self._params     = None
        self.time_format = None

    def xfer(self, cmd, expected, parameters=b"", raw=False):
        """
        Transfers cmd and data values to and returns the answer from the device.

        Args:
            cmd(str): The command to send. This is normally just an ASCII
                character.
            expected(int or str): If this is an integer, the number of expected
                bytes (in addition to the returned command character itself).
                If this is a string, then it must be the string after which to
                stop reading from the logger.
            parameters(iterable): Optional command parameters.
        Returns:
            A bytestring.
        """

        connection = serial.Serial(
            self.device,
            baudrate = 115200,
            timeout  = 5,
            parity   = serial.PARITY_NONE,
            stopbits = serial.STOPBITS_ONE)

        if not isinstance(cmd, bytes):
            cmd = cmd.encode("utf-8")
        # send command sequence
        connection.write(cmd)
        if parameters is not None:
            if not isinstance(parameters, bytes):
                parameters = parameters.encode("utf-8")
            connection.write(parameters)

        # Answer starts with the command itself.
        response = connection.read(1)
        assert response == cmd, \
            "internal: expected %s, got %s" % (cmd, response)

        if isinstance(expected, int):
            result = connection.read(expected)
        else:
            if not isinstance(expected, bytes):
                expected = expected.encode("utf-8")
            result = connection.read_until(expected)

        connection.close()

        if not raw:
            result = result.decode("utf-8")
        return result

    def __iter__(self):
        """
        Return a data block from the device. To read all data, just iterate
        over the logger instance.
        logger = Tfd500("/dev/ttyUSB0")
            for values in logger:
               for v in values:
                  <do domething with measurement point 'v'>

        Returns:
            A list of tuples. In case of temperature only logging, each tuple
            contains time and temperature. Otherwise, each tuple contains
            time, temperature and humidity.
        """
        config = self.configuration()
        number_of_points = config["count"]
        timestamp = config["start"]
        has_humidity = config["humidity"]
        delta = datetime.timedelta(seconds=config["interval"])
        block = 0
        count = 0

        while count < number_of_points:
            record = self.xfer("F", 256, "%04d" % block, True)
            data = []
            # Due to the USB protocol being block oriented, the last block
            # returned may contain more values than logged, so we need to count.
            if has_humidity:
                usable = len(record) // 3
                values = struct.unpack(">" + "hb" * usable, record[:3*usable])
                for value in zip(values[0::2], values[1::2]):
                    if count >= number_of_points:
                        break
                    data.append((timestamp, value[0] / 10.0, value[1]))
                    timestamp += delta
                    count += 1
            else:
                values = struct.unpack(">128h", record)
                for value in values:
                    if count >= config["count"]:
                        break
                    data.append((timestamp, value / 10.0))
                    timestamp += delta
                    count += 1
            block += 1
            yield data

    def is_idle(self):
        """Return True if the logger is idle, else return False."""
        result = self.xfer("a", 1)
        return result == "0"

    def is_busy(self):
        """Return True if the logger is busy, else return False."""
        return not self.is_idle()

    @property
    def time(self):
        """
        Return the logger's current clock.
        """
        _m, _i, current_date, current_time = self.xfer("o", 24).split()
        current = " ".join([current_date, current_time])
        return datetime.datetime.strptime(current, "T%d.%m.%y %H:%M:%S")

    @time.setter
    def time(self, value=None):
        """
        Set the logger's internal clock to the given time.

        Args:
            value: If "none", uses the current date and time. Otherwise, this
                must be a datetime.date (or datetime.datetime) object.
        """
        value = value or datetime.datetime.now()
        value = value.strftime("%02d.%02m.%02y %02H:%02M:%02S")
        self.xfer("T", 0, value)

    def configuration(self, item=None):
        """
        Return a dictionary (or an element from this dictionary) with the
        current logger configuration.

        Args:
            item: Either the name of an item to return or None to return the
                full dictionary.
        """
        #
        # d000010 20.07.15 11:44:56
        count, startdate, starttime = self.xfer('d', 24).split()
        start = " ".join([startdate, starttime])
        # oC1 I2 T20.07.15 12:34:56
        # The time stamp is of no use here: it's the current time
        mode, interval, _date, _time = self.xfer("o", 24).split()
        configuration = {
            'count'   : int(count),
            "start"   : datetime.datetime.strptime(start, "%d.%m.%y %H:%M:%S"),
            "humidity": int(mode[1]) > 0,
            "interval": (10, 60, 5*60)[int(interval[1])],
            }
        if item is not None:
            return configuration[item]
        return configuration

    @property
    def count(self):
        """
        Return the number of recorded data points.
        """
        return self.configuration("count")

    @property
    def start(self):
        """
        Return the recording start time (as a datetime.datetime object).
        """
        return self.configuration("start")

    @property
    def humidity(self):
        """
        Return a boolean value whether or not the humidity data has been
        recorded.
        """
        return self.configuration("humidity")

    @humidity.setter
    def humidity(self, value):
        """
        Configure humidity recording.

        Args:
            value(bool): If True, both temperature and humidity will be
                recorded. If False, only temperature will be recorded.
        """
        self.xfer("C", 0, "1" if value else "0")

    @property
    def interval(self):
        """
        Return the recording interval (in seconds).
        """
        return self.configuration("interval")

    @interval.setter
    def interval(self, value):
        """
        Configure the recording interval.

        Args:
            value(int): Number of seconds to use for the recording interval.
                The only valid values are 10, 60 and 300.
        """
        mapping = {10: "0", 60: "1", 300: "2"}
        if value not in mapping:
            raise ValueError("Invalid interval value '%s'" % value)
        self.xfer("I", 0, mapping[value])

    @property
    def version(self):
        """Return the version number string."""
        version = self.xfer('v', "\n")
        return version.strip()

    def clear_flash(self):
        """
        Clear the flash memory. Apart from the data record, this also resets
        the internal clock and deletes the last used configuration.
        """
        self.xfer("R", 0)

    def factory_reset(self):
        """
        Factory reset. Restore all factory defaults, set clock to
        01.01.00 00:00:00 and reboot.
        """
        self.xfer("X", 0)

if __name__ == "__main__":
    print("This is not the user script. Please call 'tfd500_cli.py --help'.")
