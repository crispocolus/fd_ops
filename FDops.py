#import various crap
from flask import Flask, request, render_template, session, redirect
import pandas as pd
import datetime as dt
import time
from apscheduler.schedulers.background import BackgroundScheduler
import logging

#define various crap
app = Flask(__name__)
logging.basicConfig()
sched = BackgroundScheduler()

#Google Sheets data
with open('sheet_url.txt', 'r') as file:
   	sheet_url = file.read().replace('\n', '')

#set when to reload the sheets and to refresh the web-page, in seconds)
pullCycle = int(600)
refreshCycle = int(60)

#FUNCTIONS
#stupid function to determine what row to read

def timeToRow(i):
	switcher={
	15:1,
	16:2,
	17:3,
	18:4,
	19:5,
	20:6,
	21:7,
	22:8,
	23:9,
	0:10,
	1:11,
	2:12,
	3:13,
	4:14,
	5:15,
	6:16,
	7:17,
	8:18,
	9:19,
	10:20,
	11:21,
	12:22,
	13:23,
	14:24
	}
	return switcher.get(i, "Invalid value")

#gave up on this function <- :'/
#def findRows(hour):
#	row = timeToRow(hour)
#	for hour in range(13, 14):
#		switcher={
#		13:(row, (row+1)),
#		14:(row)
#		}
#		return switcher.get(hour, row)
#	return row


#function to determine nearest minute, with resoulution <- spare for now
#def round_minutes(clock, direction, resolution):
#    	new_minute = (clock.minute // resolution + (1 if direction == 'up' else 0)) * resolution
#    	return clock + dt.timedelta(minutes=new_minute - clock.minute)

#function to determine nearest second, with resoulution
def round_seconds(clock, direction, resolution):
        new_second = (clock.second // resolution + (1 if direction == 'up' else 0)) * resolution
        return clock + dt.timedelta(seconds=new_second - clock.second)

#function to pend startup until given time
def sleepUntil():
	now = dt.datetime.now()
	startupDate = round_seconds(now, 'up', 60)
	sleepTime = ((startupDate - now).total_seconds() - 1)
	print("Waiting" + str(sleepTime) + "seconds till startup")
	time.sleep(sleepTime)

#determine clock for various uses
def determineClock():
	#determine current time
        now = dt.datetime.now()

        #determine last and next run
	global last_run
	global next_run
        last_run = now.strftime("%H:%M:%S")
        next_run = (now + dt.timedelta(seconds = (pullCycle))).strftime("%H:%M:%S")

        #finds current and nextHour
	global currentHour
	global nextHour
        currentHour = int(format(dt.datetime.today().hour))
	nextHour = int(currentHour + 1)

	#what rows to read??
	#row, rtr = findRows(currentHour)
	row = timeToRow(currentHour)
	#return last_run, next_run, row, rtr
	return last_run, next_run, row

#function for reading stuff from the sheet
def fetch_sheets_data():
	#reads the Sheet and converts to CSV
	curOps = pd.read_csv(sheet_url)

	#pickup time stuff
#	last_run,next_run,row,rtr = determineClock()
	last_run,next_run,row = determineClock()

	#defines variables
	global shack00ops
	global shack01ops
	global shack02ops
	global shack03ops
	global shack04ops
	global shack05ops
	global shackSATops

	#reads predefined rows and columns for current time-slot, converts to html-data
	shack00ops = (curOps.iloc[[row, (row+1), (row+2)], [0,1,2]]).to_html(classes='data', index=False, header=False)
	shack01ops = (curOps.iloc[[row, (row+1), (row+2)], [0,3,4]]).to_html(classes='data', index=False, header=False)
	shack02ops = (curOps.iloc[[row, (row+1), (row+2)], [0,5,6]]).to_html(classes='data', index=False, header=False)
	shack03ops = (curOps.iloc[[row, (row+1), (row+2)], [0,7,8]]).to_html(classes='data', index=False, header=False)
	shack04ops = (curOps.iloc[[row, (row+1), (row+2)], [0,9,10]]).to_html(classes='data', index=False, header=False)
	shack05ops = (curOps.iloc[[row, (row+1), (row+2)], [0,11,12]]).to_html(classes='data', index=False, header=False)
	shackSATops = (curOps.iloc[[row, (row+1), (row+2)], [0,13,14]]).to_html(classes='data', index=False, header=False)

	#test for skipping rows when time 13-14
#	ic9100ops = (curOps.iloc[[rtr, [0,1,2]]).to_html(classes='data', index=False, header=False)
#	flex6500ops = (curOps.iloc[rtr, [0,3,4]]).to_html(classes='data', index=False, header=False)
#	ic7610ops = (curOps.iloc[(rtr), [0,5,6]]).to_html(classes='data', index=False, header=False)
#	ic756ops = (curOps.iloc[(rtr), [0,7,8]]).to_html(classes='data', index=False, header=False)

#RUNTIME

#confirm the Sheets URL
print('Starting from ')
print(sheet_url)

#used to pause the script until next full minute for ease of mind
sleepUntil()

#run first time for populating tables
fetch_sheets_data()

#create scheduled task, then start schedule
sched.add_job(fetch_sheets_data,'interval', seconds=(pullCycle))
sched.start()

#makes the .html files and posts them
@app.route('/', methods=("POST", "GET"))
def ops():
    return render_template('ops.html',
	shacks=['Shack-00', 'Shack-01', 'Shack-02', 'Shack-03', 'Shack-04', 'Shack-05', 'Shack-SAT'],
       	curops=[shack00ops, shack01ops, shack02ops, shack03ops, shack04ops, shack05ops, shackSATops],
       	radios=['Flex-6500 | 20m / 160m', 'IC-7610 | 40m', 'IC756 Pro III |  80m / 15m', 'IC9100 | 10m', 'FT-891 | 60m', 'FT-450D | 80m/div', 'TS-2000 | VHF/UHF'],
       	colors=['#add19e', '#f8c491', '#c8dcf1', '#fff0c5', '#efbbbf', '#ee2288', '#e633ff'],
	links=['/shack00', '/shack01', '/shack02', '/shack03', '/shack04', '/shack05', '/shackSAT'],
	last_refresh=last_run, next_refresh=next_run,
       	hourOfDay=currentHour, nexthourOfDay=nextHour,
       	refresh=refreshCycle)

#generating single-shack timeslots

@app.route('/shack00', methods=("POST", "GET"))
def shack00_table():
        return render_template('shack00.html',
        shack='Shack-00',
        curops=[shack00ops],
        radios=['Flex-6500 | 20m / 160m'],
        colors=['#add19e'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shack01', methods=("POST", "GET"))
def shack01_table():
        return render_template('shack01.html',
        shack='Shack-01',
        curops=[shack01ops],
        radios=['IC-7610 | 40m'],
        colors=['#f8c491'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shack02', methods=("POST", "GET"))
def shack02_table():
        return render_template('shack02.html',
        shack='Shack-02',
        curops=[shack02ops],
        radios=['IC756 Pro III | 80m / 15m'],
        colors=['#c8dcf1'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shack03', methods=("POST", "GET"))
def shack03_table():
        return render_template('shack03.html',
        shack='Shack-03',
        curops=[shack03ops],
        radios=['IC-9100 | 10m'],
        colors=['#fff0c5'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shack04', methods=("POST", "GET"))
def shack04_table():
        return render_template('shack04.html',
        shack='Shack-04',
        curops=[shack04ops],
        radios=['FT-891 | 60m'],
        colors=['#efbbbf'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shack05', methods=("POST", "GET"))
def shack05_table():
        return render_template('shack05.html',
        shack='Shack-05',
        curops=[shack05ops],
        radios=['FT-450D | 80m / ymse'],
        colors=['#ee2288'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shackSAT', methods=("POST", "GET"))
def shackSAT_table():
        return render_template('shackSAT.html',
        shack='Shack-SAT',
        curops=[shackSATops],
        radios=['TS-2000 | VHF/UHF'],
        colors=['#e633ff'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

#run the Flask-app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

#stupid test for forcing 1 hour refresh <- does not work
#while (currentHour != nextHour):
#    	time.sleep(10)
#	currentHour = int(format(dt.datetime.today().hour))
#fetch_sheets_data()
#sched.shutdown()
#sched.start()

#keep the schedule running
while True:
        time.sleep(10)
sched.shutdown()

