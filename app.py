from termo_reader import TermoReader
import logging
from sensor import Sensor
from webui import TermoUI
from pathlib import Path
from datetime import timedelta,datetime

import time
import os
import sys

import yaml
import gzip
import json
from flask import Flask, render_template
import plotly

from operator import itemgetter

#for some reason on ubuntu 14.4 Path.home() fails for me
#WD=Path.home()
from os.path import expanduser
WD=expanduser('~')
 
CONF_FILE=Path(WD, ".temperature.conf")
DATA_DIR= Path(WD, "temperature")

DATE_CACHE_SIZE = timedelta(days=1).total_seconds()
logging.basicConfig(level=logging.INFO)
sensors = []

app = Flask(__name__)

def formatTimeDate(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

@app.route("/")
def hello():
    graphs = []
    ids = []
    for s in sensors:
        keys = sorted(s.data.keys())
        keysAsDates = [formatTimeDate(x) for x in keys]
        values = itemgetter(*keys)(s.data)
        ids.append("Teplota {} [C]".format(s.name))
        logging.debug("for %s keys: %s values %s", s.name, keysAsDates, values)
        graph = dict(
            data=[
                dict(
                    x = keysAsDates,
                    y = values,
                    name = s.name,
                    type='scatter'
                ),
            ],
            layout=dict(
                    title=s.name
            )
        )
        graphs.append(graph)
        # Add "ids" to each of the graphs to pass up to the client

    # Convert the figures to JSON
    # PlotlyJSONEncoder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', ids=ids, graphJSON=graphJSON)


if ( not CONF_FILE.exists()):
    logging.error("Configuration file %s do not exists", str(CONF_FILE))
    sys.exit(-1)

if ( not DATA_DIR.exists() or not DATA_DIR.is_dir()):
    logging.error("Working directory %s do not exists, make sure it created and accesible", str(DATA_DIR))
    sys.exit(-1)


with open(str(CONF_FILE)) as f:
    # use safe_load instead load
    #sensors = yaml.safe_load(f)
    configuration = yaml.load(f)
    for s in configuration['sensors']:
        sensor = Sensor(**s)
        sensor.setDataFile(str(Path(DATA_DIR, sensor.name + ".csv.gz")))
        sensors.append(sensor)

logging.info("succesfully load configuration: %s from %s", sensors, str(CONF_FILE) )

logging.info("reading previous state")

limit = time.time()-DATE_CACHE_SIZE
for s in sensors:
    i = 0
    logging.info(" reading previous state for %s from %s", s.name, s.dataFile)
    if (Path(s.dataFile).exists()):
        with gzip.open(s.dataFile, "rt") as dataFile:
            for line in dataFile:
                parts = line.split(",")
                if(len(parts)!=2):
                    logging.waring("Corupted line: %s, ignoring", line)
                    continue
                timestamp = float(parts[0])

                if(limit < timestamp):
                    s.addData(timestamp, float(parts[1]))
                    i += 1

            logging.info("for sensor %s there was %d data records restored", s.name, i)


logging.info("staring sensor read loop")
reader = TermoReader(sensors)
reader.start()

logging.info("starting web ui")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
