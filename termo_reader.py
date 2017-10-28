import threading
import gzip
import time
import logging
from datetime import timedelta,datetime

SLEEP_SECONDS=60

class TermoReader(threading.Thread):

    def __init__(self, sensors, dao):
        threading.Thread.__init__(self, daemon=True)
        self.sensors = sensors
        self.dao = dao

    def run(self):
        while True:
            for s in self.sensors:
                try:
                    newTemp = self.readTemperature(s) + s.compensation
                    newTime = time.time()
                    timeFormated = self.formatTimeDate(newTime)
                    logging.info("Sensor: name %s: %s : %s",s.name, timeFormated, newTemp)
                    self.dao.addData(s.name, newTime, timeFormated, newTemp)
                except TemperatureReadException as ex:
                    logging.warning(ex)
            time.sleep(SLEEP_SECONDS)

    def formatTimeDate(self, timestamp):
        return str(datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S'))

    def readTemperature(self, sensor):
        """ read temperature in C"""
        temp=None;
        with open(sensor.file) as f:
            for line in f:
                for item in line.split():
                    if("t=" in item):
                        temp=float(item.replace("t=",""))/1000
        if(temp == None):
            raise TemperatureReadException("unable to read temperature for %s from %s" % (sensor.name, sensor.file))
        return temp

class TemperatureReadException(Exception):
    pass
