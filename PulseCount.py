import RPi.GPIO as GPIO
import time
from datetime import datetime
import os
import requests
import json
import shelve

#threaded call-back function, executed whenever a falling edge is detected.
def pulse(channel):
	global pulse_count
	pulse_count+=1

# time_str = '11/20/2015 14:43:50:693'
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
def smap_post(sourcename, smap_value, path, uuid, units): #prior smap_value was x, y
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
    r = requests.post(smap_url, data=data_json, headers=http_headers, verify=False)
    return r.text

#smap constants
smap_sourcename = 'Turnberry'
path = '/Furnace_NaturalGas'
uuid_pulse_count = 'e38eed0a-2ccc-11e6-a012-acbc32bae629'
uuid_pulse_diff = 'eac7f466-2ccc-11e6-a8d0-acbc32bae629' #this is the one I've used so far.
units = 'count'

#local data storage and shelve file paths
historyFile = '/home/pi/Documents/PulseCount/count_data.csv'
cumFile = '/home/pi/Documents/PulseCount/cum_count.txt'
shelveFile = '/home/pi/Documents/PulseCount/smap_post.db'

#open shelve file for persistent python object storage
shelf = shelve.open(shelveFile)

#test if object keys already exist, if not, create them.
if not shelf.has_key('smap_value'):
	shelf['smap_value'] = []

#Assign values to pulse_count, diff_pulse and old_count.
#If cumFile exists, open it for reading. Set pulse_count value based on file value.
if(os.path.exists(cumFile)==True):
	cum = open(cumFile, 'r')
	dat = cum.read()
	pulse_count = int(dat)	
	cum.close()
#If file does not exist, just assign pulse_count to 0. 	
else:
	pulse_count = 0

old_count = pulse_count 
diff_pulse = 0

#pin identification system to use
GPIO.setmode(GPIO.BCM)

#set up GPIO27 pin as input, with RPi internal pull-down resistor set to keep it in a digital 'ON'
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Interrupt added to GPIO27 pin, execute pulse() whenever falling edge is detected.
GPIO.add_event_detect(27, GPIO.FALLING, callback=pulse)

def main():

	#instantiate global variables, so function affects values outside of function namespace.
	global diff_pulse
	global old_count	
	global pulse_count

	#infinite loop with 60-second delay.
	while True:
		#Open data files for writing values.
		cum = open(cumFile, 'w') #this will overwrite whatever the prior value is.
		datacsv = open(historyFile, 'a') #this will append without overwriting prior data.
		#Calculate pulses in current minute
		diff_pulse = pulse_count - old_count
		old_count = pulse_count #update old_count
		DT = datetime.now()
		TimeStr = DT.strftime('%Y-%m-%d %H:%M:%S')
		#Write values to files.
		datacsv.write(TimeStr + ',' + str(pulse_count) + ',' + str(diff_pulse) + '\n')
		cum.write(str(pulse_count))
		#Close data files
		cum.close()
		datacsv.close()
		
		print 'Total pulses counted = %i; recent pulses = %i' %(pulse_count, diff_pulse)

		#Place current values in persistent python object storage using shelve.
		#If shelve has values in it, they are posted to smap database.
		#If the post is successful, the values are removed from the object. 
		#If not successful, values remain for next iteration of main().
		shelf['smap_value'] += [[time_str_to_ms(TimeStr), diff_pulse]]
		
		if shelf['smap_value']:
			response = smap_post(smap_sourcename, shelf['smap_value'], path, uuid_pulse_diff, units)
			if not response:
				shelf['smap_value'] = []
			#for smap_value in shelf['smap_value']:
				#response = smap_post(smap_sourcename, smap_value, path, uuid_pulse_diff, units)
				#if not response:
					#shelf.remove(smap_value)
		#I have some concerns about the timing of this, when integrating the smap posting/shelf elements. 
		#I've tested on my laptop, posting a single value, took 0.0071 seconds, which should not cause much disruption.		
		time.sleep(60)

if __name__ == "__main__":
	main()
	
# 	
# 	
# 	
# >>> shelf = []
# >>> shelf += [[time_str_to_ms('2016-06-07 10:00:00'), 20]]
# >>> shelf
# [[1465318800000L, 20]]
# >>> shelf += [[time_str_to_ms('2016-06-07 10:01:00'), 22]]
# >>> shelf += [[time_str_to_ms('2016-06-07 10:02:00'), 24]]
# >>> shelf += [[time_str_to_ms('2016-06-07 10:03:00'), 26]]	
# 
# smap_post(smap_sourcename, shelf, path, uuid_pulse_diff, units)
# 
# if shelf:
# 	for smap_value in shelf:
# 		response = smap_post(smap_sourcename, smap_value, path, uuid_pulse_diff, units)
# 
# if shelf['smap_value']:
# 	response = smap_post(smap_sourcename, shelf['smap_value'], path, uuid_pulse_diff, units)
# 	if not response:
# 		shelf['smap_value'] = []
