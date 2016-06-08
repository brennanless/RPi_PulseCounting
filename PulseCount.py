import RPi.GPIO as GPIO
import time
from datetime import datetime
import os

#threaded call-back function, executed whenever a falling edge is detected.
def pulse(channel):
	global pulse_count
	pulse_count+=1
	
def datetime_to_int(dt):
	return '%s%s%s%s.csv' %(dt.strftime('%Y'), dt.strftime('%m'), dt.strftime('%d'), dt.strftime('%H'))  

# smap constants
# smap_sourcename = 'Turnberry'
# path = '/Furnace_NaturalGas'
# uuid_pulse_count = 'e38eed0a-2ccc-11e6-a012-acbc32bae629'
# uuid_pulse_diff = 'eac7f466-2ccc-11e6-a8d0-acbc32bae629' #this is the one I've used so far.
# units = 'count'

#local data storage and shelve file paths
historyFilepath = '/home/pi/Documents/PulseCount/data/'
cumFile = '/home/pi/Documents/PulseCount/cum_count.txt'
#shelveFile = '/home/pi/Documents/PulseCount/smap_post.db'

#Assign values to pulse_count, diff_pulse and old_count.
#If cumFile exists, open it for reading. Set pulse_count value based on file value.
if(os.path.exists(cumFile)==True):
	with open(cumFile, 'r') as cum:
		dat = cum.read()
		pulse_count = int(dat)	
		#cum.close() #Still needed?
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
	
# 	open shelve file for persistent python object storage
# 	with shelve.open(shelveFile) as shelf:
# 		shelf = shelve.open(shelveFile)
# 		test if object keys already exist, if not, create them.
# 		if not shelf.has_key('smap_value'):
# 			shelf['smap_value'] = []

	#infinite loop with 60-second delay.
	while True:
	
		dt = datetime.now() 
		filename = datetime_to_int(dt)
		historyFile = os.path.join(historyFilepath, filename)
		
		#Open data files for writing values.
		with open(cumFile, 'w') as cum, open(historyFile, 'a') as datacsv:
			#cum = open(cumFile, 'w') #this will overwrite whatever the prior value is.
			#datacsv = open(historyFile, 'a') #this will append without overwriting prior data.
			#Calculate pulses in current minute
			diff_pulse = pulse_count - old_count
			old_count = pulse_count #update old_count
			DT = datetime.now()
			TimeStr = DT.strftime('%Y-%m-%d %H:%M:%S')
			#Write values to files.
			datacsv.write(TimeStr + ',' + str(pulse_count) + ',' + str(diff_pulse) + '\n')
			cum.write(str(pulse_count))
			#Close data files
			#cum.close()
			#datacsv.close()

		#print 'Total pulses counted = %i; recent pulses = %i' %(pulse_count, diff_pulse)

		time.sleep(60)

		#Place current values in persistent python object storage using shelve.
		#If shelve has values in it, they are posted to smap database.
		#If the post is successful, the values are removed from the object. 
		#If not successful, values remain for next iteration of main().
	# 		shelf['smap_value'] += [[time_str_to_ms(TimeStr), diff_pulse]]
	# 	
	# 		if shelf['smap_value']:
	# 			response = smap_post(smap_sourcename, shelf['smap_value'], path, uuid_pulse_diff, units)
	# 			if not response:
	# 				shelf['smap_value'] = [] #Empty the list if upload to smap was successful. 
			#for smap_value in shelf['smap_value']:
				#response = smap_post(smap_sourcename, smap_value, path, uuid_pulse_diff, units)
				#if not response:
					#shelf.remove(smap_value)
		#I have some concerns about the timing of this, when integrating the smap posting/shelf elements. 
		#I've tested on my laptop, posting a single value, took 0.0071 seconds, which should not cause much disruption.		
		#time.sleep(60)

if __name__ == "__main__":
	main()
