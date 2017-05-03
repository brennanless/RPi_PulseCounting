#This script checks if the data directory has a current data file in it.
#If empty, that means the python script is not working for some reason.

import os

#List files in the data directory.
files = os.listdir('/home/pi/Documents/PulseCount/data/')

#Remove the archive and .DS_Store listings.
for name in ['archive', '.DS_Store']:
    if name in files: files.remove(name)

#If remaining list is empty (daq not running), then issue reboot command.
if not files:
    os.system('reboot')
    

