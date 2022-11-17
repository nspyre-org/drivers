# Drivers
This is a set of Python drivers for lab instrumentation. These drivers are 
associated with [nspyre](https://nspyre.readthedocs.io/en/latest/), but are 
also suitable for general usage. Unless otherwise specified, drivers are 
provided under the terms of the MIT license.

## Installation

```bash
pip install nspyre-drivers
```

Certain drivers require extra dependencies. Those dependencies can be installed 
by specifying a tag during the install. E.g. to install the DLI pdu driver 
dependencies, use:

```bash
pip install nspyre-drivers[dli_pdu]
```

A full listing of the tags is below.

```
beaglebone
dli_pdu
oceanoptics
ximea
zaber
```

For some USB drivers on Linux, you need to grant user access to the drivers in 
order for VISA to detect them:
You should find the udev rules file in the same folder as the driver, then, e.g.:

```bash
sudo cp src/drivers/thorlabs/cld1010/99-thorlabs-cld1010.rules /etc/udev/rules.d/
````

Create a user group for the usb device access:

```bash
sudo groupadd usbtmc
```

Add any relevant users to the group:

```bash
usermod -aG usbtmc <myuser>
```

Reboot for the changes to take effect.

## Usage

After installation, you can use drivers with, e.g.:

```python
from drivers.rohde_schwarz.hmp4040.hmp4040 import HMP4040
with HMP4040('TCPIP::192.168.0.10::5025::SOCKET') as power_supply:
	# set the power supply channel 1 to 5V
	power_supply.set_voltage(1, 5.0)
```

See the source for all of the available drivers and the import paths.

## Other Drivers

In order to minimize reinventing the wheel, below is a list of other sources of 
python instrument drivers. Please contribute if you find other useful sources!

[pycobolt](https://github.com/cobolt-lasers/pycobolt)

## Contributing

If you want to contribute driver code, please submit it as a 
[pull request](https://nspyre.readthedocs.io/en/latest/contributing.html#forking-pull-requests). This project uses 
[poetry](https://python-poetry.org/). If your driver requires specific 
dependencies beyond those currently in use in the project, you should include 
them in the pyproject.toml file as extras. See the poetry documentation for 
specifics on how to declare these dependencies.
