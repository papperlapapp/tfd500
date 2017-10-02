#!/usr/bin/python

"""
Controlling the ELV TFD500 data logger via Python.
"""

# Prepare for python 3.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

# Standard imports
from textwrap import dedent
import argparse
import datetime
import math
import os
import sys

# Project imports.
from tfd500 import Tfd500
from progress import ProgressBar


def cmd_status(logger, args):
    """
    Return and optionally print the current logger status.
    """
    idle = logger.is_idle()
    if not args.silent:
        if idle:
            print("IDLE")
        else:
            print("BUSY")
    return 0 if idle else 1


def cmd_configuration(logger, _args):
    """
    Print the logger's current configuration.
    """
    recording = logger.is_busy()
    config = logger.configuration()
    print(dedent("""
        Status:       {}
        Start:        {}
        Interval:     {}
        Mode:         temperature {}
        # of records: {}
        """.format(
            "recording" if recording else "NOT recording",
            config["start"],
            config["interval"],
            "plus humidity" if config["humidity"] else "only",
            "unknown" if recording else config["count"]
            )))


def cmd_set_clock(logger, args):
    """
    Set the logger's internal clock.
    """
    if args.value is None:
        stamp = datetime.datetime.now()
    else:
        stamp = None
    logger.time = stamp


def cmd_get_clock(logger, _args):
    """
    Print the logger's interval clock.
    """
    print(logger.time.ctime())


def cmd_configure(logger, args):
    """
    Configure the logger's settings.
    """
    mapping = {
        "10s": 10,
        "60s": 60,
        "1m": 60,
        "300s": 300,
        "5m": 300,
        }
    logger.time = datetime.datetime.now()
    logger.interval = mapping.get(args.interval, "300")
    logger.humidity = args.humidity


def cmd_clear_flash(logger, _args):
    """
    Clear the logger's flash memory.
    """
    logger.clear_flash()


def cmd_factory_reset(logger, _args):
    """
    Perform a factory reset.
    """
    logger.factory_reset()


def cmd_version(logger, _args):
    """
    Print the logger's version.
    """
    print(logger.version)


def dewpoint(temperature, humidity):
    """
    Approximate dew point calculation.

    Args:
        temperature: temperature in degrees celsius
        humidity: relative humidity in percent
    Returns:
        A tuple consisting of the dew point and the absolute humidity.
    """
    # pylint:disable=C0103
    AI = 7.45
    BI = 235.0
    z1 = (AI * temperature) / (BI + temperature)
    es = 6.1 * math.exp(z1 * 2.3025851)
    e = es * humidity / 100
    z2 = e / 6.1
    z3 = 0.434292289 * math.log(z2)
    # pylint:enable=C0103
    dew = (235.0 * z3) / (7.45 - z3)
    hum = (216.7 * e) / (273.15 + temperature)
    return dew, hum

def _format_record(data_format, count, stamp, temperature, humidity):
    """
    Return a nicely formatted data record.

    Args:
        data_format (str): The format string describing the desired result.
        count (int): Running record number.
        stamp(str): The formatted time stamp.
        temperature(float): Temperature in degrees Celsius
        humidity(int): Relative humidity in percent.
    Returns:
        A nicely formatted string.
    """
    record = data_format
    record = record.replace("%c", "%s" % count)
    record = record.replace("%d", "%s" % stamp)
    record = record.replace("%t", "%4.1f" % temperature)
    record = record.replace("%f", "%4.1f" % (1.8 * temperature + 32.0))
    if humidity is not None:
        # %h = relative humidity
        record = record.replace("%h", "%d" % humidity)
        # %a = absolute humidity
        dew, humidity = dewpoint(temperature, humidity)
        record = record.replace("%a", "%4.1f" % humidity)
        # %w = dew point in degrees Celsius
        record = record.replace("%w", "%4.1f" % dew)
        # %o = dew point in degrees Fahrenheit
        record = record.replace("%o", "%4.1f" % (1.8 * dew + 32.0))
    record = record.replace("%p", "%")
    return record

def _open_output(args, config):
    if args.output == '-':
        output = sys.stdout
        args.no_progress = True
    else:
        if args.output is None:
            filename = config["start"].strftime("tfd500-%Y%m%d.csv")
            print("Data will be written to file '%s'" % filename)
        else:
            filename = args.output
        if os.path.exists(filename) and not args.force:
            print("'%s' already exists; use -f to force overwrite" % filename)
            sys.exit(1)
        output = open(filename, 'w')
    return output


def cmd_dump(logger, args):
    """
    Dump recorded values into a file or to stdout.
    """
    if logger.is_busy():
        print("Logger is currently recording.")
        return 1
    config = logger.configuration()
    if config["count"] == 0:
        print("No records available (nothing has been logged).")
        return 0
    output = _open_output(args, config)
    progress = None if args.no_progress else ProgressBar(config['count'])
    if args.data_format:
        data_format = args.data_format
    else:
        data_format = "%c;%d;%t"
        if config["humidity"]:
            data_format += ";%h"
    counter = 0
    for values in logger:
        for value in values:
            stamp, temp, hum = value
            record = _format_record(
                data_format,
                counter,
                stamp.strftime(args.time_format),
                temp,
                hum if config["humidity"] else None)
            print(record, file=output)
            counter += 1
        if progress is not None:
            progress += len(values)
    if progress is not None:
        print()
    return 0


def parse_args(args):
    """
    Parse the command line arguments and return a parsed version of them.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--device", "-d",
        default="/dev/ttyUSB0",
        help="Path to the serial device. Defaults to /dev/ttyUSB0 if missing.")

    subparsers = parser.add_subparsers(
        title="Available commands",
        description="Type <command> --help for help on individual command")

    subparser = subparsers.add_parser(
        "version",
        help="Print the logger's software version.")
    subparser.set_defaults(func=cmd_version)

    subparser = subparsers.add_parser(
        "set-clock",
        help="Set the logger's internal real-time clock. Normally, there's no"
             " need to explicitly running this command: when you configure the"
             " logger, it's internal clock will be set automatically.")
    subparser.add_argument(
        "--value",
        help="Optional time to use. If missing, uses the current date and time.")
    subparser.set_defaults(func=cmd_set_clock)

    subparser = subparsers.add_parser(
        "get-clock",
        help="Get the value of the logger's internal real-time clock.")
    subparser.set_defaults(func=cmd_get_clock)

    subparser = subparsers.add_parser(
        "factory-reset",
        help="Perform a factory reset. All data records and settings"
             " will be lost.")
    subparser.set_defaults(func=cmd_factory_reset)

    subparser = subparsers.add_parser(
        "configuration",
        help="Print the logger's current configuration")
    subparser.set_defaults(func=cmd_configuration)

    subparser = subparsers.add_parser(
        "configure",
        help="Configure the logger.")
    subparser.add_argument(
        "--interval", "-i",
        choices=("10s", "60s", "1m", "300s", "5m"),
        default="5m",
        help="Selects the desired recording interval.")
    subparser.add_argument(
        "--humidity", "-u",
        action="store_true",
        help="If True, record humidity in addition to the temperature."
             " Without this option, only the temperature will be recorded.")
    subparser.set_defaults(func=cmd_configure)

    subparser = subparsers.add_parser(
        "status",
        help="Print and return the logger's status. The program's exit code is"
             " 0 when the logger is idle. If the logger is currently recording,"
             " the exit code will be 1.")
    subparser.add_argument(
        "--silent", "--quiet", "-s", "-q",
        action="store_true",
        help="If given, nothing will be printed; only the exit code will"
             " indicate the logger's status")
    subparser.set_defaults(func=cmd_status)

    subparser = subparsers.add_parser(
        "dump",
        help="Dump the recorded data.")
    subparser.add_argument(
        "--output", "-o",
        help="Name of output file to use. If '-', will dump o stdout. If"
             " missing, will construct a file name using the logger's start"
             " date.")
    subparser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Without this argument, existing files will not be overwritten.")
    subparser.add_argument(
        "--no-progress", "-p",
        action="store_true",
        help="Suppress printing the progress bar. This option will be"
             " implicitly set when the output goes to stdout.")
    subparser.add_argument(
        "--time-format", "-t",
        default="%d.%m.%Y %H:%M:%S",
        help="Format to use for printing time values. The given string will be"
             " directly passed to strftime().")
    subparser.add_argument(
        "--data-format", "-d",
        help="Format to use for the data records. Within the format string, the"
             " following sequences will have special meanings: %%p will be"
             " replaced with a percent sign; %%c will be replaced with the data"
             " point number, starting at zero; %%d will be replaced with the"
             " date/time for the data point (see --time-format); %%t will be"
             " replaced with the temperature value in degrees Celsius; %%h will"
             " be replaced with the relative humidity; %%f will be replaced with"
             " the temperature in degrees Fahrenheit; %%a will be replaced"
             " with the absolute humidity value; %%w will be replaced with the"
             " dew point in degrees Celsius and %o will be replaced with the"
             " dew point in degrees Fahrenheit."
             " The default value if this option is omitted is '%%c;%%d;%%t' for"
             " temperature only recordings and '%%c;%%d;%%t;%%h' for recordings"
             " with temperature and humidity.")
    subparser.set_defaults(func=cmd_dump)

    subparser = subparsers.add_parser(
        "clear-flash",
        help="Clear the flash memory. This removes all data records.")
    subparser.add_argument(
        "--keep-settings", "-k",
        action="store_true",
        help="Keep previous configuration settings and time. Without this"
             " option, the previous settings and the clock will be reset too.")
    subparser.set_defaults(func=cmd_clear_flash)

    subparser = subparsers.add_parser(
        "factory-reset",
        help="Reset the logger to factory settings.")
    subparser.set_defaults(func=cmd_factory_reset)

    args = parser.parse_args(args)
    return args


def main(args):
    """Main program."""
    args = parse_args(args)
    logger = Tfd500(args.device)
    result = args.func(logger, args) or 0
    sys.exit(result)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
