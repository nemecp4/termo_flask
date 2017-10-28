from termo_reader import TermoReader
from TermoDao import TermoDao
import logging
from sensor import Sensor
from pathlib import Path
from datetime import timedelta,datetime

import sys

import yaml
import json
from flask import Flask, render_template
import plotly

#for some reason on ubuntu 14.4 Path.home() fails for me
#WD=Path.home()
from os.path import expanduser
WD=expanduser('~')

CONF_FILE=Path(WD, ".temperature.conf")
DATA_DIR= Path(WD, "temperature")
DB_FILE=Path(DATA_DIR, "meteo.db")

DATE_CACHE_SIZE = timedelta(days=1).total_seconds()
logging.basicConfig(level=logging.INFO)
sensors = []

app = Flask(__name__)

@app.route("/")
def webui():
    graphs = []
    ids = []
    sixHours = (datetime.now() - timedelta(hours = 6)).timestamp()
    graphs.append(getGraph(sixHours, ""))
    ids.append("Teplota za poslednich 6 hodin [C]")

    fiveDays = (datetime.now() - timedelta(days = 5)).timestamp()
    graphs.append(getGraph(fiveDays, ""))

    ids.append("Teplota za poslednich 5 dni [C]")
    # Convert the figures to JSON
    # PlotlyJSONEn  coder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    status ={}
    for s in sensors:
        status[s.name]=dao.getCurrentTemperatue(s.name)
    return render_template('index.html', ids=ids, sensorStatus=status, graphJSON=graphJSON)

def getGraph(timeStamp, label):
    # generate plotly graph structure
    graph = dict(
           data=[],
           layout=dict(title=label))
    for s in sensors:
        rows = dao.readDataNewerThan(s.name, timeStamp)
        keysAsDates = [x[0] for x in rows]
        values = [x[1] for x in rows]
        graph.get('data').append(
            dict(
                   x = keysAsDates,
                   y = values,
                   name = s.name,
                   type='scatter'
            ))
    return graph

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

dao = TermoDao(str(DB_FILE), sensors)

logging.info("staring sensor read loop")
reader = TermoReader(sensors, dao)
reader.start()

logging.info("starting web ui")
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
