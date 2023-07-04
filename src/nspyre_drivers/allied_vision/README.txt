Allied Vision Vimba X installation (on linux):
- First, install Vimba X: https://www.alliedvision.com/en/products/software/vimba-x-sdk/
- Extract the tarball to, e.g., /opt
- To install the driver:
	cd <install dir>/cti
	sudo ./VimbaUSBTL_Install.sh (for USB cameras)
- Reboot
- The CTI file (needed for genicam related acquisition) is <install dir>/cti/VimbaUSBTL.cti
- To install the python API "vmbpy":
	cd <install dir>/api/python/
	pip install ./vmbpy*.whl
