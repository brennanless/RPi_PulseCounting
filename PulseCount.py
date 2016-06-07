import RPi.GPIO as GPIO
import time
from datetime import datetime
import os

uuid_pulse_count = 'xyz'
uuid_pulse_diff = 'abc'

historyFile = '/home/pi/Documents/PulseCount/count_data.csv'
cumFile = '/home/pi/Documents/PulseCount/cum_count.txt'

if(os.path.exists(cumFile)==True):
	cum = open(cumFile, 'r')
	dat = cum.read()
	pulse_count = int(dat)	
	cum.close()
else:
	pulse_count = 0

old_count = pulse_count 
diff_pulse = 0

GPIO.setmode(GPIO.BCM)

GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def pulse(channel):
	global pulse_count
	pulse_count+=1

GPIO.add_event_detect(27, GPIO.FALLING, callback=pulse)

def main():

	global diff_pulse
	global old_count	
	global pulse_count

	while True:
		cum = open(cumFile, 'w')
		datacsv = open(historyFile, 'a')
		diff_pulse = pulse_count - old_count
		DT = datetime.now()
		TimeStr = DT.strftime('%Y-%m-%d %H:%M:%S')
		datacsv.write(TimeStr + ',' + str(pulse_count) + ',' + str(diff_pulse) + '\n')
		cum.write(str(pulse_count))
		print 'Total pulses counted = %i; recent pulses = %i' %(pulse_count, diff_pulse)
		old_count = pulse_count
		cum.close()
		datacsv.close()
		time.sleep(60)

if __name__ == "__main__":
	main()
