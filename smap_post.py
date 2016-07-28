import time
from datetime import datetime
import os
import requests
import json
import pandas as pd


kWh_perPulse_WattNode = 0.00015
kWh_perPulse_Gas = 0.2998242

NVac = 120. #nominal line voltage
PpPO = 3. #phases per pulse output
CTamps = 15. #amperage rating of current transducer
FSHz = 10. #full-scale pulse frequency
CTmultiplier = 1. #this is because wer are monitoring only one leg of the 2-leg circuit

#pass a list of counts, convert each count to a frequency, return list
def pulseFreq(count):
	freq = []
	for val in range(len(count)):
		freq.append(count[val]/60.)
	return freq

def power(pulse_freq):
	global NVac
	global PpPO
	global CTamps
	global FSHz
	global CTmultiplier
	pow = []
	for val in range(len(pulse_freq)):
		pow.append(CTmultiplier * (NVac * PpPO * CTamps * pulse_freq[val]) / FSHz)
	return pow

def time_str_to_ms(time_str):
    pattern = "%Y-%m-%d %H:%M:%S"
    try:
        epoch = int(time.mktime(time.strptime(time_str, pattern)))
    except ValueError:
        print "time_str_to_ms(): Unexpected input -> %s" % time_str
        raise
    return int(epoch*1000)

#smap_post() function takes ipnuts and sends data to smap database on LBNL remote server.
#smap_value is a list of lists (date in ms and value).
def smap_post(sourcename, smap_value, path, uuid, units, timeout): #prior smap_value was x, y
    smap_obj = {}
    smap_obj[path] = {}
    metadata = {}
    metadata['SourceName'] = sourcename
    metadata['Location'] = {'City': 'Fresno'}
    smap_obj[path]["Metadata"] = metadata
    smap_obj[path]["Properties"] = {"Timezone": "America/Los_Angeles",
                                    "UnitofMeasure": units,
                                    "ReadingType": "double"}
    smap_obj[path]["Readings"] = smap_value # previously:[smap_value], [x,y]
    smap_obj[path]["uuid"] = uuid
    data_json = json.dumps(smap_obj)
    http_headers = {'Content-Type': 'application/json'}
    #smap_url = "https://render04.lbl.gov/backend/add/vQRmOWwffl65TRkb4cmj3jWfDiPsglwy4Bog"
    smap_url = "https://rbs-box2.lbl.gov/backend/add/vQRmOWwffl65TRkb4cmj3jWfDiPsglwy4Bog"
    r = requests.post(smap_url, data=data_json, headers=http_headers, verify=False, timeout=timeout)
    return r.text
    
def file_to_int(file):
	return int(file.split('.')[0])    
	
def datetime_to_int(dt):
	valstr = '%s%s%s%s' %(dt.strftime('%Y'), dt.strftime('%m'), dt.strftime('%d'), dt.strftime('%H'))
	return int(valstr)
	
#     
# #local data storage and shelve file paths
# historyFile = '/home/pi/Documents/PulseCount/count_data.csv'
# cumFile = '/home/pi/Documents/PulseCount/cum_count.txt'
# shelveFile = '/home/pi/Documents/PulseCount/smap_post.db'  
  
    
#smap constants
smap_sourcename = 'Turnberry'
#smap_path = '/Furnace_NaturalGas'
sensor_paths = ['/Furnace_CH4-rate_cum', '/Furnace_CH4-rate', '/HVAC_blower_energy_cum', '/HVAC_blower_energy', '/HVAC_blower_power']
sensor_uuids = ['bf7476b0-3d84-11e6-8672-acbc32bae629', 'c6f8fc61-3d84-11e6-a61f-acbc32bae629', 'ccdb58c7-3d84-11e6-9699-acbc32bae629', 'd2b1c34a-3d84-11e6-b723-acbc32bae629', '60292b6e-54f3-11e6-b278-acbc32bae629']
sensor_units = ['kWh', 'kWh', 'kWh', 'kWh', 'kW']
timeout = 10

path = '/home/pi/Documents/PulseCount/data/'
#path = '/Users/brennanless/GoogleDrive/Attics_CEC/DAQ/RPi_PulseCounting/data/'
#archive_path = '/Users/brennanless/GoogleDrive/Attics_CEC/DAQ/RPi_PulseCounting/data/archive/'
archive_path = '/home/pi/Documents/PulseCount/data/archive/'
os.chdir(path) #change working directory to path
#all files in pwd except those beginning with '.', such as mac .DS_store files.
files = []
for item in os.listdir(path):
    if not item.startswith('.') and os.path.isfile(os.path.join(path, item)):
        files.append(item)
#files = os.listdir(path) #list files in path

dt = datetime.now() 
val_now = datetime_to_int(dt)

for file in range(len(files)):
	val = file_to_int(files[file])
	if(val == val_now):
		continue
	else:
		#if(val < val_now):	
		data = pd.read_csv(files[file], header=None, dtype = {0:str, 1:float, 2:float, 3:float, 4:float})
		data = data.dropna()
		times = []
		times_as_list = data[data.columns[0]].tolist() #extracts the date-time column as a list. 
		pow = power(pulseFreq(data[data.columns[4]].tolist()))
		data['power'] = pow #append column to dataframe
		#Convert column of datetimes to Unix timestamps in msec
		for i in range(len(times_as_list)):
			times.append(time_str_to_ms(times_as_list[i]))
		#zips each data column with the Unix timestamp list, creating a nested list.
		count = 0
		for col in range(len(data.columns)-1):
			data_as_list = data[data.columns[col+1]].tolist()
			if col < 2:
				data_as_list = [x * kWh_perPulse_Gas for x in data_as_list]
			else if col >= 2 & col <4:
				data_as_list = [x * kWh_perPulse_WattNode for x in data_as_list]
			smap_value = zip(times, data_as_list)
			#this creates a nested list-of-lists, from the original list of tuples [[],[]] vs. [(), ()].
			for i in range(len(smap_value)):
				smap_value[i] = list(smap_value[i])   
			try:	     
				response = smap_post(smap_sourcename, smap_value, sensor_paths[col], sensor_uuids[col], sensor_units[col], timeout)
			except requests.exceptions.ConnectionError:	
				print 'Connection error, will try again later.'
			if not response:
				count += 1
		if count == 5:
			os.rename(path + files[file], archive_path + files[file]) #moves posted file to 'archive' directory.
					
