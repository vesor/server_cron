

import sys, os
import subprocess
import logging
from logging import handlers
from datetime import datetime, timedelta
import re
import dateutil.parser

work_dir = os.path.dirname(sys.argv[0])
script_name = os.path.basename(sys.argv[0])

logger = logging.getLogger(script_name)
log_filename = os.path.join(work_dir, script_name.split('.')[0] + '.log')
hdlr = logging.handlers.RotatingFileHandler(log_filename, maxBytes=5*1024*1024, backupCount=2)
#hdlr = logging.FileHandler(log_filename)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

def get_load_avg():
    f = open("/proc/loadavg")
    loadavg = f.read().split()
    f.close()
    return loadavg[:3] # load avg of 1, 5, 15min

def is_idle():
    loadavg = os.getloadavg()
    logger.info('getloadavg: %s', loadavg)
    load_thresh = 0.2
    idle = (loadavg[0] < load_thresh and loadavg[1] < load_thresh and loadavg[2] < load_thresh)
    return idle

def is_wakeup_recently():
    last_wakeup_log = None
    with open('/var/log/kern.log') as logfile:
        for line in logfile:
            if line.find(' PM: suspend exit') != -1:
                last_wakeup_log = line
    
    if last_wakeup_log is None:
        return False

    #print('log:',line)
    re_obj = re.search('^[^ ]+ [^ ]+ [^ ]+ ', last_wakeup_log)
    #print('re', re_obj.group(), '$')
    event_time = dateutil.parser.parse(re_obj.group())
    #print('dt',event_time)
    delta = datetime.now()-event_time
    #print('delta', delta)

    logger.info('is_wakeup_recently: %s,%s', event_time, delta)

    if delta > timedelta(minutes=5):
        return False
    else:
        return True
    

def time_to_next_wakeup(now):
    now_hour = now.hour + now.minute / 60.0 + now.second / 3600.0
    
    wakeup_hours = [9, 12, 20, 21, 22, 23]
    if now.weekday() == 5 or now.weekday() == 6: # weekends
        wakeup_hours = [i for i in range(9, 24)]

    wakeup_hours = list(set(wakeup_hours)) # remove duplicates
    wakeup_hours.sort()
    #print ('now thresh', (now_hour + 5 / 60.0) % 24)
    next_hour = None
    for h in wakeup_hours:
        if (now_hour + 5 / 60.0) % 24 < h:
            next_hour = h
            break
    if next_hour is None:
        next_hour = wakeup_hours[0]
    
    if next_hour > now_hour:
        time_to_next = (next_hour - now_hour) * 3600
    else:
        time_to_next = (next_hour + (24 - now_hour)) * 3600
    #print("now =", now_hour, next_hour, time_to_next)
    logger.info('time_to_next_wakeup: %s,%s', now_hour, next_hour)

    return time_to_next

def rtcwake(seconds):
    #cmd = ['ls', '-l', 'abcde']
    cmd = ['rtcwake', '-m', 'mem', '-s', str(int(seconds))]
    logger.info('subprocess.Popen: %s', cmd)
    MyOut = subprocess.Popen(cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
    stdout,stderr = MyOut.communicate()
    logger.info('subprocess.Popen stdout: %s', stdout)
    logger.info('subprocess.Popen stderr: %s', stderr)
    #print(stdout.decode("utf-8"))
    #print(stderr)

def main():
    #now = datetime(2020, 5, 30, 22, 55, 12)
    #time_to_next_wakeup(now)
    if is_idle() and not is_wakeup_recently():
        now = datetime.now()
        sec = time_to_next_wakeup(now)
        rtcwake(sec)

if __name__ == "__main__":
    main()
