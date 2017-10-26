import sqlite3 as lite
import logging

# crude always-on db layer
class TermoDao:
    def __init(self, dbFile, sensors):
        self.dbFile = dbFile
        try:
            con = lite.connect(self.dbFile)
            cur = con.cursor()
            for s in sensors:
                logging.info("checking meteo table %s " % s.name)
                con.execute ("CREATE TABLE IF NOT EXISTS %s ((timestamp integer primary key, temperature double))" % s.name)
        finally:
            if con:
                con.close();
