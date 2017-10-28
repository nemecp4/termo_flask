import sqlite3 as lite
import logging

# crude always-on db layer
class TermoDao:
    def __init__(self, dbFile, sensors):
        self.dbFile = dbFile
        self.lastTemperature={}
        con = None
        try:
            con = lite.connect(self.dbFile)
            cur = con.cursor()
            for s in sensors:
                logging.info("checking meteo table %s " % s.name)
                con.execute ("CREATE TABLE IF NOT EXISTS %s (timestamp integer primary key, timestampFormated string, temperature double)" % s.name)
        finally:
            if con:
                con.close();

    def addData(self, sensorName, timestamp, timestampFormated, temperature):
        con = None
        self.lastTemperature[sensorName]=temperature
        try:
            con = lite.connect(self.dbFile)
            cur = con.cursor()
            cur.execute("INSERT INTO %s values(%d, '%s', %f)" % (sensorName, timestamp, timestampFormated, temperature))
            con.commit()
        finally:
            if con:
                con.close()
    def readDataNewerThan(self, name, timestamp):
        con = None
        try:
            con = lite.connect(self.dbFile)
            cur = con.cursor()
            query = "SELECT timeStampFormated, temperature FROM %s WHERE timestamp > %d ORDER BY timestamp;" % (name, timestamp)
            logging.info(query)
            cur.execute(query)
            return cur.fetchall();
        finally:
            if con:
                con.close()

    def getCurrentTemperatue(self, sensorName):
        con = None
        try:
            con = lite.connect(self.dbFile)
            cur = con.cursor()
            query = "SELECT max(timestamp), timeStampFormated, temperature FROM %s ORDER BY timestamp;" % (sensorName)
            logging.info(query)
            cur.execute(query)
            items = cur.fetchone();
            print(items[2])
            return items[2]
        finally:
            if con:
                con.close()
