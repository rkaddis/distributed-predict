# /usr/bin/bash

sudo echo
pip install --break-system-packages -r requirements.txt worker
sudo ln -s distributed-worker.service /etc/systemd/system/
sudo systemctl enable distributed-worker.service
sudo systemctl daemon-reload
echo "Installation complete. Reboot to start the worker service."