Driver update for CP210x
========================

As of Linux kernel 4.14rc2, the TFD500's USB to serial converter chip is not
yet recognized by the kernel (a patch has been sent and accepted). As long
as you're running an older kernel, you'll need the updated driver from this
directory. The driver itself has been tested on Fedora 26 only (kernel 4.12.13).

Update: as of January 2018, the patch is already part of kernel releases 3.18,
4.4, 4.9 and 4.13.

Driver Installation with DKMS
-----------------------------

The modified driver can be built and installed using DKMS.

DKMS (Dynamic Kernel Module Support) enables generating Linux kernel modules
outside the kernel source tree. It rebuilds the modules automatically when a
new kernel is installed.

Copy the content of this repository to `/usr/src/cp210x-1.0.0`, the run the
following commands to install the DKMS module:

::

    # dkms add cp210x/1.0.0
    # dkms build cp210x/1.0.0
    # dkms install cp210x/1.0.0

If the cp210x kernel module was already loaded before running the above
commands, you need to unload the old module and reload the new module once via

::

    # rmmod cp201x
    # modprobe cp210x

To later remove the module (when the modified driver is part of your kernel):

::

    # dkms remove cp210x/1.0.0 --all
