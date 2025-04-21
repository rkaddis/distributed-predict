# /usr/bin/bash

sudo echo
pip install --break-system-packages -r requirements.txt worker
input=""
read -p "Install as a service? [Y/n]: " input
if [[ input == "y" ]]
then
sudo ln -s distributed-worker.service /etc/systemd/system/
sudo systemctl enable distributed-worker.service
sudo systemctl daemon-reload
fi
echo "Installation complete. Reboot to start the worker service."