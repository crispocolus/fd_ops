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
        last_run = now.strftime("%H:%M")
        next_run = (now + dt.timedelta(seconds = (refreshCycle))).strftime("%H:%M")

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
	global ic9100ops
	global flex6500ops
	global ic7610ops
	global ic756ops
#	global ts2000ops

	#reads predefined rows and columns for current time-slot, converts to html-data
	ic9100ops = (curOps.iloc[[row, (row+1), (row+2)], [0,1,2]]).to_html(classes='data', index=False, header=False)
	flex6500ops = (curOps.iloc[[row, (row+1), (row+2)], [0,3,4]]).to_html(classes='data', index=False, header=False)
	ic7610ops = (curOps.iloc[[row, (row+1), (row+2)], [0,5,6]]).to_html(classes='data', index=False, header=False)
	ic756ops = (curOps.iloc[[row, (row+1), (row+2)], [0,7,8]]).to_html(classes='data', index=False, header=False)
#	ts2000ops = (curOps.iloc[[timeRow, (timeRow+1), (timeRow+2)], [0,9,10]]).to_html(classes='data', index=False, header=False)

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
#sleepUntil()

#run first time for populating tables
fetch_sheets_data()

#create scheduled task, then start schedule
sched.add_job(fetch_sheets_data,'interval', seconds=(pullCycle))
sched.start()

#makes the .html files and posts them
@app.route('/', methods=("POST", "GET"))
def ops():
    return render_template('ops.html',
	shacks=['Shack-00', 'Shack-01', 'Shack-02', 'Shack-03'],
       	curops=[ic9100ops, flex6500ops, ic7610ops, ic756ops],
       	radios=['IC-9100 | 40m', 'Flex-6500 | 160 / 20m', 'IC-7610 | 80m / 15m', 'IC756 Pro III |  60m / 10m'],
       	colors=['#add19e', '#f8c491', '#c8dcf1', '#fff0c5'],
	links=['/shack00', '/shack01', '/shack02', '/shack03'],
	last_refresh=last_run, next_refresh=next_run,
       	hourOfDay=currentHour, nexthourOfDay=nextHour,
       	refresh=refreshCycle)

#generating single-shack timeslots
@app.route('/shack00', methods=("POST", "GET"))
def shack00_table():
    	return render_template('shack00.html',
	shack='Shack-00',
        curops=[ic9100ops],
        radios=['IC-9100 | 40m'],
        colors=['#add19e'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shack01', methods=("POST", "GET"))
def shack01_table():
        return render_template('shack01.html',
        shack='Shack-01',
        curops=[flex6500ops],
        radios=['Flex-6500 | 160 / 20m'],
        colors=['#f8c491'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shack02', methods=("POST", "GET"))
def shack02_table():
        return render_template('shack02.html',
        shack='Shack-02',
        curops=[ic7610ops],
        radios=['IC-7610 | 80m / 15m'],
        colors=['#c8dcf1'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

@app.route('/shack03', methods=("POST", "GET"))
def shack03_table():
        return render_template('shack03.html',
        shack='Shack-03',
        curops=[ic756ops],
        radios=['IC756 Pro III | 60m / 10m'],
        colors=['#fff0c5'],
        last_refresh=last_run, next_refresh=next_run,
        hourOfDay=currentHour, nexthourOfDay=nextHour,
        refresh=refreshCycle)

#@app.route('/shack04', methods=("POST", "GET"))
#def shack04_table():
#        return render_template('shack04.html',
#        shack='Shack-04',
#        curops=[ts2000ops],
#        radios=['TS-2000 | 60m / 10m'],
#        colors=[''],
#        last_refresh=last_run, next_refresh=next_run,
#        hourOfDay=currentHour, nexthourOfDay=nextHour,
#        refresh=refreshCycle)

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

