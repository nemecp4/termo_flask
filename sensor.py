class Sensor:
    """ hold info about sensors """
    def __init__(self, **entries):
        self.__dict__.update(entries)
        self.data = {}

    def addData(self, timestamp, temperature):
        self.data[timestamp] = temperature
    def setDataFile(self, dataFile):
        self.dataFile = dataFile
