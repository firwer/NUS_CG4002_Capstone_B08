@echo off
:: This script is used to deploy the ext_comms folder to the remote server rapidly.

echo Zipping the ext_comms folder...
powershell Compress-Archive -Path ext_comms, int_comms -DestinationPath ext_comms.zip -Force

echo Transferring the zip file to the remote server...
scp ext_comms.zip xilinx@172.26.190.199:/home/xilinx/

echo Unzipping the folder on the remote server...
ssh xilinx@172.26.190.199 "cd /home/xilinx/ && unzip -o ext_comms.zip && rm ext_comms.zip"

echo Cleaning up the local zip file...
del ext_comms.zip

echo Deployment complete!
pause