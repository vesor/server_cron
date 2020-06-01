
'''
use "sudo crontab -e" to add a task for this script:
for example, every 5 min:

*/5 * * * * sudo python3 /media/data/server_cron/check_idle.py

'''

import sys, os
import subprocess
import logging
from logging import handlers
from datetime import datetime, timedelta
import re
import dateutil.parser, time

work_dir = os.path.join(os.path.dirname(sys.argv[0]), 'data')
if not os.path.exists(work_dir):
    os.makedirs(work_dir)

script_name = os.path.basename(sys.argv[0])

logger = logging.getLogger(script_name)
log_filename = os.path.join(work_dir, script_name.split('.')[0] + '.log')
hdlr = logging.handlers.RotatingFileHandler(log_filename, maxBytes=5*1024*1024, backupCount=2)
#hdlr = logging.FileHandler(log_filename)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)


def is_idle():
    loadavg = os.getloadavg()
    logger.info('getloadavg: %s', loadavg)
    load_thresh = 0.5
    idle = (loadavg[0] < load_thresh and loadavg[1] < load_thresh and loadavg[2] < load_thresh)
    return idle

# lock (disable) idle checking. no sleep at all. 
def is_locked():
    return os.path.exists(os.path.join(work_dir, 'lock'))

# check this to avoid sleep immediately after wakeup
def is_wakeup_recently():
    try:
        waketime_ts = os.path.getmtime(os.path.join(work_dir, 'wakeup'))
        waketime = datetime.fromtimestamp(waketime_ts)
    except:
        return False
    
    #print ('waketime', waketime)
    
    delta = datetime.now()-waketime
    #print('delta', delta)

    logger.info('is_wakeup_recently: %s,%s', waketime, delta)

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

def run_cmd(cmd):
    logger.info('subprocess.Popen: %s', cmd)
    MyOut = subprocess.Popen(cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
    stdout,stderr = MyOut.communicate()
    if stdout is not None and len(stdout) > 0:
        logger.info('subprocess.Popen stdout: %s', stdout.decode("utf-8"))
    if stderr is not None and len(stderr) > 0:
        logger.info('subprocess.Popen stderr: %s', stderr.decode("utf-8"))
    #print(stdout.decode("utf-8"))
    #print(stderr)

def rtcwake(seconds):
    #cmd = ['ls', '-l', '.']
    run_cmd(['rtcwake', '-m', 'mem', '-s', str(int(seconds))])
    run_cmd(['touch', os.path.join(work_dir, 'wakeup')])

def main():
    #now = datetime(2020, 5, 30, 22, 55, 12)
    #time_to_next_wakeup(now)
    if not is_locked() and is_idle() and not is_wakeup_recently():
        now = datetime.now()
        sec = time_to_next_wakeup(now)
        rtcwake(sec)

if __name__ == "__main__":
    main()
