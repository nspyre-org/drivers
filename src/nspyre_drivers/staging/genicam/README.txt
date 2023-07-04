The driver requires a "genTL" driver backend to be installed. Follow
the instructions from your camera manufacturer to install their driver.

Below are instructions for how to get some specific camera drivers installed:

Allied Vision Vimba X (on linux):
- First, install Vimba X: https://www.alliedvision.com/en/products/software/vimba-x-sdk/
- extract the tarball to, e.g., /opt
- cd to <install dir>/cti
- sudo ./VimbaUSBTL_Install.sh (for USB cameras)
- reboot
- cti file is <install dir>/cti/VimbaUSBTL.cti
