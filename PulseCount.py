import RPi.GPIO as GPIO
import time
from datetime import datetime
import os

#threaded call-back function, executed whenever a falling edge is detected.
def pulse_1(channel):
	global pulse_count_1
	pulse_count_1+=1
	
def pulse_2(channel):
	global pulse_count_2
	pulse_count_2+=1	
	
#function takes a datetime.now() object and creates a file name string formatted as 'YYYYMMDDHH.csv'	
def datetime_to_filepath(dt):
	return '%s%s%s%s.csv' %(dt.strftime('%Y'), dt.strftime('%m'), dt.strftime('%d'), dt.strftime('%H'))  

#local data storage file paths
historyFilepath = '/home/pi/Documents/PulseCount/data/'
cumFile_1 = '/home/pi/Documents/PulseCount/cum_count_1.txt'
cumFile_2 = '/home/pi/Documents/PulseCount/cum_count_2.txt'

#Assign values to pulse_count_1, diff_pulse_1 and old_count_1.
#If cumFile exists, open it for reading. Set pulse_count_1 value based on file value.
#If file is empty, set to 0, if file does not exist, set to 0.
if(os.path.exists(cumFile_1)==True):
	with open(cumFile_1, 'r') as cum_1:
		dat = cum_1.read()
		if(len(dat)==0):
			pulse_count_1 = 0
		else:
			pulse_count_1 = int(dat)	
else:
	pulse_count_1 = 0
	
old_count_1 = pulse_count_1 
diff_pulse_1 = 0	
	
if(os.path.exists(cumFile_2)==True):
	with open(cumFile_2, 'r') as cum_2:
		dat = cum_2.read()
		if(len(dat)==0):
			pulse_count_2 = 0
		else:
			pulse_count_2 = int(dat)	
else:
	pulse_count_2 = 0	

old_count_2 = pulse_count_2
diff_pulse_2 = 0

#pin identification system to use
GPIO.setmode(GPIO.BCM)

#set up GPIO27 and GPIO18 pins as input, with RPi internal pull-down resistor set to keep it in a digital 'ON'
#pulse1 values are for the Air Handler
#pulse2 values are for the Compressor
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Interrupt added to GPIO27 pin, execute pulse() whenever falling edge is detected.
GPIO.add_event_detect(27, GPIO.FALLING, callback=pulse_1)
GPIO.add_event_detect(18, GPIO.FALLING, callback=pulse_2)

def main():

	#instantiate global variables, so function affects values outside of function namespace.
	global diff_pulse_1
	global old_count_1	
	global pulse_count_1
	global diff_pulse_2
	global old_count_2	
	global pulse_count_2
	
	start_time = time.time()
	
	#infinite loop with 60-second delay.
	while True:
		dt = datetime.now() 
		filename = datetime_to_filepath(dt)
		historyFile = os.path.join(historyFilepath, filename)
		
		#Open data files for writing values.
		try:
			with open(cumFile_1, 'w') as cum_1, open(cumFile_2, 'w') as cum_2, open(historyFile, 'a') as datacsv:
				#Calculate pulses in current minute
				diff_pulse_1 = pulse_count_1 - old_count_1
				old_count_1 = pulse_count_1 #update old_count_1
				diff_pulse_2 = pulse_count_2 - old_count_2
				old_count_2 = pulse_count_2 #update old_count_2
				DT = datetime.now()
				TimeStr = DT.strftime('%Y-%m-%d %H:%M:%S')
				#Write values to files.
				datacsv.write(TimeStr + ',' + str(pulse_count_1) + ',' + str(diff_pulse_1) + ',' + str(pulse_count_2) + ',' + str(diff_pulse_2) + '\n')
				cum_1.write(str(pulse_count_1))	
				cum_2.write(str(pulse_count_2))
		except:
			start_time += 60
			time.sleep(start_time - time.time())

		#print 'Total pulses counted = %i; recent pulses = %i' %(pulse_count_1, diff_pulse_1)
		#print 'Total pulses counted = %i; recent pulses = %i' %(pulse_count_2, diff_pulse_2)
		
		start_time += 60
	
		time.sleep(start_time - time.time())


if __name__ == "__main__":
	main()
