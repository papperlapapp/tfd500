Quick start
===========

Configure recording for 5min interval, temperature only:

::

   ./tfd500_cli.py configure --interval 5m

Configure recording for 1min interval, temperature and humidity:

::

   ./tfd500_cli.py configure --interval 1m --humidity

Set the logger's internal clock:

::

   ./tfd500_cli.py setclock

Write recorded data points to a file, using the time and date format of the
current locale. The filename will be automatically determined from the
recorded data:

::

   ./tfd500_cli.py dump --time-fmt "%c"

Write recorded data points to the standard output, using the default date/time
format, but change the data format to ``<date><tab><temperature><tab><humidity>``
instead of the original CSV format (which is ``%c;%d;%t;%h``):

::

   ./tfd500_cli.py dump --output - --data-fmt="%d\t%t\t%h"

Show the current configuration:

::

   ./tfd500_cli.py configuration

Print the logger's software version:

::

   ./tfd500_cli.py version


Full commandline documentation
==============================

In the following, all options are described. Some of them have a short
alternative. See output of ``--help`` for a complete list.

Global command line options
---------------------------

``--help``
    Print some help.

``--device <device>``
    The device to be used. Use this when the device is not on ``/dev/ttyUSB0``.

Commands
--------

``version``
    Print the logger's software version.

``set-clock``
    Set the logger's internal real-time clock. Normally, there's no need to
    explicitly running this command: when you configure the logger, it's
    internal clock will be set automatically.

``get-clock``
    Get the value of the logger's internal real-time clock.

``configuration``
    Print the logger's current configuration.

``configure``
    Configure the logger.

    ``--interval {10s,60s,1m,300s,5m}``, ``-i {10s,60s,1m,300s,5m}``
        Selects the desired recording interval. Defaults to 5m if missing.

    ``--humidity``, ``-u``
        If given, record humidity in addition to the temperature. Without this
        option, only the temperature will be recorded.

``status``
    Print and return the logger's status. The program's exit code is ``0`` when
    the logger is idle. If the logger is currently recording, the exit code will
    be ``1``.

    `--silent`, `--quiet`, `-s`, `-q`
        If given, nothing will be printed; only the exit code will indicate the
        logger's status

``dump``
    Dump the recorded data.

    ``--output OUTPUT``, ``-o OUTPUT``
        Name of output file to use. If '-', will dump o stdout. If missing, will
        construct a file name from the logger's start date.

    ``--force``, ``-f``
        Without this argument, existing files will not be overwritten.

    ``--no-progress``, ``-p``
          Suppress printing the progress bar. This option will be implicitly set
          when the output goes to stdout.

    ``--time-format TIME_FORMAT``, ``-t TIME_FORMAT``
        Format to use for printing time values. The given string will be
        directly passed to strftime().

    ``--data-format DATA_FORMAT``, ``-d DATA_FORMAT``
        Format to use for the data records. Within the format string, the
        following sequences have special meanings:

        ========   ==================================
        sequence   replacement
        ========   ==================================
           %p      a percent sign
           %c      data point number, starting at zero
           %d      date/time for the data point
           %t      temperature in degrees Celsius
           %h      relative humidity
           %f      temperature in degrees Fahrenheit
           %a      absolute humidity value
           %w      dew point in degrees Celsius
           %o      dew point in degrees Fahrenheit
        ========   ==================================

        If the option is omitted, it defaults to ``%c;%d;%t`` for temperature
        only recordings and ``%c;%d;%t;%h`` for recordings with both temperature
        and humidity.

``factory-reset``
    Perform a factory reset. All data records and settings will be lost.

``clear-flash``
    Clear the flash memory. This removes all data records.


See ``./tfd500_cli.py --help`` for an up-to-date list of all available
commands.
