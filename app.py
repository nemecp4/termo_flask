from termo_reader import TermoReader
from TermoDao import TermoDao
import logging
from sensor import Sensor
from pathlib import Path
from datetime import timedelta,datetime

import sys, optparse

import yaml
import json
from flask import Flask, render_template
import plotly

CONF_FILE='/etc/temperature.conf'
DATA_DIR= '/var/lib/temperature/'
DB_FILE=Path(DATA_DIR, "meteo.db")

DATE_CACHE_SIZE = timedelta(days=1).total_seconds()
sensors = []

# global dao referenced from webui
dao = None
app = Flask(__name__)

@app.route("/")
def webui():
    graphs = []
    ids = []
    currentDateTime = datetime.now()
    sixHours = (currentDateTime - timedelta(hours = 6)).timestamp()
    graphs.append(getGraph(sixHours, "6 hodin [°C]"))
    ids.append("Teplota za poslednich 6 hodin [C]")

    fiveDays = (currentDateTime - timedelta(days = 5)).timestamp()
    graphs.append(getGraph(fiveDays, "5 dni [°C]"))

    ids.append("Teplota za poslednich 5 dni [°C]")
    # Convert the figures to JSON
    # PlotlyJSONEn  coder appropriately converts pandas, datetime, etc
    # objects to their JSON equivalents
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)
    status ={}
    for s in sensors:
        status[s.name]=dao.getCurrentTemperatue(s.name)
    return render_template('index.html', ids=ids, sensorStatus=status, updateTime=currentDateTime, graphJSON=graphJSON)

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
                   description = "ahoj",
                   type='scatter'
            ))
    return graph


def main(arg):
    logging.basicConfig(level=logging.DEBUG)
    parser = optparse.OptionParser()
    parser.add_option('-c',
        '--configuration',
        dest='configuration',
        default=CONF_FILE)
    options, remainder = parser.parse_args()

    logging.info("configuration: "+options.configuration)

    if ( not Path(options.configuration).exists()):
        logging.error("Configuration file %s do not exists", str(CONF_FILE))
        sys.exit(-1)

    if ( not Path(DATA_DIR).exists() or not Path(DATA_DIR).is_dir()):
        logging.error("Working directory %s do not exists, make sure it created and accesible", str(DATA_DIR))
        sys.exit(-1)


    with open(options.configuration) as f:
        # use safe_load instead load
        #sensors = yaml.safe_load(f)
        configuration = yaml.load(f)
        for s in configuration['sensors']:
            sensor = Sensor(**s)
            sensor.setDataFile(str(Path(DATA_DIR, sensor.name + ".csv.gz")))
            sensors.append(sensor)

    logging.info("succesfully load configuration: %s from %s", sensors, str(CONF_FILE) )
    global dao
    dao = TermoDao(str(DB_FILE), sensors)

    logging.info("staring sensor read loop")
    reader = TermoReader(sensors, dao)
    reader.start()

    logging.info("starting web ui")
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=8080)


main(sys.argv)
