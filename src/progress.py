"""
A simple progress bar.

Example usage:

>>> maxvalue = 100
... bar = ProgressBar(maxvalue)
... for i in range(maxvalue):
...     do_something()
...     bar += 1
"""

# Standard imports.
import sys


class ProgressBar(object):
    """
    A simple progress bar class.
    """
    def __init__(self, maxvalue, length=60):
        """
        Args:
            maxvalue(float,int): The value representing 100%.
            length(int): The length of the progress bar.
        """
        self.currentvalue = 0
        self.percent = ""
        self.maxvalue = float(maxvalue)
        self.length = length
        self.reset()

    def reset(self, newvalue=0):
        """
        Reset the progress bar.

        Args:
            newvalue(float,int): The new progress bar value.
        """
        self.currentvalue = float(newvalue)
        percent = 100.0 * self.currentvalue / self.maxvalue
        self.percent = "%.1f%%" % percent
        self.draw(init=True)

    def draw(self, init=False):
        """
        This method actually draws the progress bar. There's no need to call
        the method explicitly. Just add your increment to the object.
        """
        percent = 100.0 * self.currentvalue / self.maxvalue
        bar = "=" * int(self.length * percent / 100.0)
        percent = "%.1f%%" % percent
        if init or percent != self.percent:
            self.percent = percent
            bar += " " * (self.length - len(bar))
            sys.stdout.write("\r[{0}] {1}".format(bar, percent))
            sys.stdout.flush()

    def __iadd__(self, increment):
        self.currentvalue += increment
        self.draw()
        return self
