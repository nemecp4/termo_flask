import threading
import gzip
import time
import logging
SLEEP_SECONDS=1

class TermoReader(threading.Thread):

    def __init__(self, sensors):
        threading.Thread.__init__(self, daemon=True)
        self.sensors = sensors

    def run(self):
        while True:
            for s in self.sensors:
                newTemp = self.readTemperature(s)
                newTime = time.time()
                with gzip.open(s.dataFile, "at") as dataFile:
                    dataFile.write("{0}, {1}\n".format(newTime, newTemp))
                s.addData(newTime, newTemp)
                logging.debug("Sensor: name %s: %s : %s",s.name, newTime, newTemp)
            time.sleep(SLEEP_SECONDS)

    def readTemperature(self, sensor):
        """ read temperature in C"""
        temp=-1;
        with open(sensor.file) as f:
            for line in f:
                for item in line.split():
                    if("t=" in item):
                        temp=float(item.replace("t=",""))/1000
        return temp
