import RPi.GPIO as GPIO
import time
from datetime import datetime
import os

#threaded call-back function, executed whenever a falling edge is detected.
def pulse(channel):
	global pulse_count
	pulse_count+=1
	
#function takes a datetime.now() object and creates a file name string formatted as 'YYYYMMDDHH.csv'	
def datetime_to_filepath(dt):
	return '%s%s%s%s.csv' %(dt.strftime('%Y'), dt.strftime('%m'), dt.strftime('%d'), dt.strftime('%H'))  

#local data storage file paths
historyFilepath = '/home/pi/Documents/PulseCount/data/'
cumFile = '/home/pi/Documents/PulseCount/cum_count.txt'

#Assign values to pulse_count, diff_pulse and old_count.
#If cumFile exists, open it for reading. Set pulse_count value based on file value.
#If file is empty, set to 0, if file does not exist, set to 0.
if(os.path.exists(cumFile)==True):
	with open(cumFile, 'r') as cum:
		dat = cum.read()
		if(len(dat)==0):
			pulse_count = 0
		else:
			pulse_count = int(dat)	
else:
	pulse_count = 0

old_count = pulse_count 
diff_pulse = 0

#pin identification system to use
GPIO.setmode(GPIO.BCM)

#set up GPIO27 pin as input, with RPi internal pull-down resistor set to keep it in a digital 'ON'
#pulse1 channel is set for gas meter reading.
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Interrupt added to GPIO27 pin, execute pulse() whenever falling edge is detected.
GPIO.add_event_detect(27, GPIO.FALLING, callback=pulse, bouncetime=50)

def main():

	#instantiate global variables, so function affects values outside of function namespace.
	global diff_pulse
	global old_count	
	global pulse_count

	start_time = time.time()

	#infinite loop with 60-second delay.
	while True:
		#start_time = time.time()
		dt = datetime.now() 
		filename = datetime_to_filepath(dt)
		historyFile = os.path.join(historyFilepath, filename)
		
		#Open data files for writing values.
		try:
			with open(cumFile, 'w') as cum, open(historyFile, 'a') as datacsv:
				#Calculate pulses in current minute
				diff_pulse = pulse_count - old_count
				old_count = pulse_count #update old_count
				DT = datetime.now()
				TimeStr = DT.strftime('%Y-%m-%d %H:%M:%S')
				#Write values to files.
				datacsv.write(TimeStr + ',' + str(pulse_count) + ',' + str(diff_pulse) + '\n')
				cum.write(str(pulse_count))
		except:
			start_time += 60
			time.sleep(start_time - time.time())
			continue
						
		#print 'Total pulses counted = %i; recent pulses = %i' %(pulse_count, diff_pulse)
		start_time += 60
		time.sleep(start_time - time.time())


if __name__ == "__main__":
	main()
