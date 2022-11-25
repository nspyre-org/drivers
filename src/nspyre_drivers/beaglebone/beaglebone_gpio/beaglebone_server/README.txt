# set up the beaglebone to be powered from the 5V DC barrel jack (don't use USB)
# connect ethernet
# connect to beaglebone with sftp and transfer the server files
sftp debian@beaglebone.local
> put -R beaglebone_server
# connect to the beaglebone with ssh
ssh debian@beaglebone.local
# run on the beaglebone:
sudo ln -s /home/debian/beaglebone_server/gpio_flask_server.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable gpio_flask_server.service
sudo systemctl start gpio_flask_server.service
# to confirm it's working it should be "active" according to
sudo systemctl status gpio_flask_server.service