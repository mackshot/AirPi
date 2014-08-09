from . import output
import datetime
import time
from . import calibration
import os

class Print(output.Output):
    requiredparams = ["format"]
    optionalparams = ["calibration", "metadata"]

    def __init__(self, params):
        self.cal = calibration.Calibration.sharedclass
        self.docal = self.checkcal(params)
        self.format = params['format']

    def outputmetadata(self):
        metadata = self.getmetadata()
        toprint  = "Run started: " + metadata['starttime'] + os.linesep
        toprint += "Operator: " + metadata['operator'] + os.linesep
        toprint += "Raspberry Pi name: " + metadata['piname'] + os.linesep
        toprint += "Raspberry Pi ID: " +  metadata['piid']
        return toprint

    def outputdata(self, datapoints):
        if self.docal == 1:
            datapoints = self.cal.calibrate(datapoints)
        if self.format == "csv":
            theoutput = "\"" + time.strftime("%Y-%m-%d %H:%M:%S") + "\","
            for i in datapoints:
                theoutput += str(i['value']) + ","
                theoutput = theoutput[:-1]
                print(theoutput)
        else:
            print(("Time".ljust(17)) + ": " + time.strftime("%Y-%m-%d %H:%M:%S"))
            for i in datapoints:
                if i['name'] == "Location":
                    # print i['name'] + ": " + "Disposition:" + i['disposition'] + "Elevation: " + i['altitude'] + "Exposure: " + i['exposure'] + "Latitude: " + i['latitude'] + "Longitude: " + i['longitude']
                    pprint(i)
                else:
                    thevalue = i['value']
                    if type(thevalue) is float:
                        if thevalue > 10000:
                            thevalue = int(round(i['value'], 0))
                        elif thevalue > 1000:
                            thevalue = round(i['value'], 1)
                        else:
                            thevalue = round(i['value'], 2)
                print((i['name'].ljust(17)).replace("_", " ") + ": " + str(thevalue).ljust(8) + " " + i['symbol'])
            print("==========================================================")
        return True
