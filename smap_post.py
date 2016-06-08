import time
from datetime import datetime
import os
import requests
import json
import pandas as pd

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
    smap_url = "https://render04.lbl.gov/backend/add/vQRmOWwffl65TRkb4cmj3jWfDiPsglwy4Bog"
    r = requests.post(smap_url, data=data_json, headers=http_headers, verify=False, timeout=timeout)
    return r.text
    
def file_to_int(file):
	return int(file.strip('.')[0])    
	
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
path = '/Furnace_NaturalGas'
uuid_pulse_count = 'e38eed0a-2ccc-11e6-a012-acbc32bae629'
uuid_pulse_diff = 'eac7f466-2ccc-11e6-a8d0-acbc32bae629' #this is the one I've used so far.
units = 'count'
timeout = 1

path = '/home/pi/Documents/PulseCount/data/'
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
	if(val < val_now):	
		data = pd.read_csv(files[file], header=None)
		data = data.dropna()
		times = []
		times_as_list = data[data.columns[0]].tolist() #extracts the date-time column as a list. 
		#Convert column of datetimes to Unix timestamps in msec
		for i in range(len(times_as_list)):
			times.append(time_str_to_ms(times_as_list[i]))
		#zips each data column with the Unix timestamp list, creating a nested list.
		#for col in range(len(data.columns)-2):
		#Be sure to set this to retrieve whatever data you want, most likely the pulse_diff values.
		#for col in range(2):
		#If data.columns[] is set to 1, the the cumulative count is reported, 
		#if set to 2, then the diff_pulse value is returned.
		data_as_list = data[data.columns[2]].tolist()
		smap_value = zip(times, data_as_list)
		#this creates a nested list-of-lists, from the original list of tuples [[],[]] vs. [(), ()].
		for i in range(len(smap_value)):
			smap_value[i] = list(smap_value[i])   
		try:	     
			response = smap_post(smap_sourcename, smap_value, path, uuid_pulse_diff, units, timeout)
		except requests.exceptions.ConnectionError:	
			print 'Connection error, will try again later.'
		if not response:
			os.rename(path + files[file], archive_path + files[file]) #moves posted file to 'archive' directory.
			        
		
# 
# 
# 
# smap_value = [[time_str_to_ms('2016-06-08 12:16:00'), 47]]
# 
# while count <= 10:
# 	try:
# 		response = smap_post(smap_sourcename, smap_value, path, uuid_pulse_diff, units, timeout)
# 	except requests.exceptions.ConnectionError:
# 		print 'Connection has timed out, will try again in one minute.'
# 
# dt = datetime.now()    
# 
# val_now = datetime_to_int(dt)
# 
# if(dt.minute == 0):
# 	historyFile = '/home/pi/Documents/PulseCount/%s%s%s%s.csv' %(dt.strftime('%Y'), dt.strftime('%m'), dt.strftime('%d'), dt.strftime('%H'))
# with open(historyFile) as datacsv:
# 	...

		
