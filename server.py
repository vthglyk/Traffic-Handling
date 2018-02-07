"""
Executed with: FLASK_APP=server.py flask  run
"""
import redis
import subprocess
import os
import sys
import atexit
import requests
import time
import logging
import json

from flask import Flask, Response

OAM_URL = os.environ['oam_url']
TRAFFIC_HANDLING_PERIOD = os.environ['traffic_handling_period'] if os.environ['traffic_handling_period'] else 10 
TRAFFIC_HANDLING_STARTED = 'STARTED'
TRAFFIC_HANDLING_STOPPED = 'STOPPED'
RESENDING_OAM_REQUEST_PERIOD = 10
CELERY_WORKER_NAME = "celery_worker"
HEADERS = {'content-type': 'application/json'}

rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

fileHandler = logging.FileHandler("logs/server.log")
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
rootLogger.addHandler(consoleHandler)


def exit_handler():
    # Kill celery_worker screen

    try:
        print subprocess.check_output(["kill", "-9"], shell=False)
        print subprocess.check_output(["screen", "-ls"], shell=False)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            screen_id = None
            for i in e.output.split():
                if CELERY_WORKER_NAME in i:
                    screen_id = i
                    subprocess.call(["screen", "-X", "-S", screen_id, "quit"], shell=False)
            if screen_id:
                logging.info("Celery_worker screen FOUND: {}".format(screen_id))
            else:
                logging.info("Celery_worker screen NOT FOUND")

        else:
            raise RuntimeError("command '{}' return with code ({}) and output:\n {}".format(e.cmd,
                                                                                            e.returncode,
                                                                                            e.output))

    # Inform OAM that traffic handling module stopped

    logging.info('My application is ENDING!')
    payload = {'action': TRAFFIC_HANDLING_STOPPED, 'period_s': int(TRAFFIC_HANDLING_PERIOD)}
    ending_req = requests.put(OAM_URL, headers=HEADERS,
                              data=json.dumps(payload))
    while ending_req.status_code != 200:
        logging.info('Could not contact OAM. Resending request')
        time.sleep(RESENDING_OAM_REQUEST_PERIOD)
        ending_req = requests.put(OAM_URL, headers=HEADERS,
                                  data=json.dumps(payload))

    logging.info("OAM was informed successfully for the cancellation of the traffic handling module")


atexit.register(exit_handler)
app = Flask(__name__)
r = redis.StrictRedis(host='localhost', port=6379, db=0)
dir_path = os.getcwd()

logging.debug("Working directory is: " + dir_path)

# Inform OAM that traffic handling module started
payload = {'action': TRAFFIC_HANDLING_STARTED, 'period_s': int(TRAFFIC_HANDLING_PERIOD)}

starting_req = requests.put(OAM_URL, headers=HEADERS,
                            data=json.dumps(payload))
logging.debug("oam_url = " + OAM_URL)
logging.info("traffic_handling_period = " + str(TRAFFIC_HANDLING_PERIOD))
if starting_req.status_code != 200:
    logging.info("Could not contact OAM")
    sys.exit()
else:
    logging.info("OAM was contacted successfully")

# Start process
process = subprocess.Popen(["screen", "-S", CELERY_WORKER_NAME, "-d", "-m", os.getcwd() + "/start_celery_worker.sh"], shell=False, cwd=dir_path)
logging.debug("The pid of the child process is " + str(process.pid))


@app.route("/rules")
def rules():
    resp = Response(r.get("rules"))
    resp.headers['Content-Type'] = 'application/json'
    return resp


app.run(host='0.0.0.0')
