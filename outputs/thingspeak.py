from . import output
import requests
from . import calibration

class Thingspeak(output.Output):
    requiredparams = ["APIKey","needsinternet"]
    optionalparams = ["calibration"]

    def __init__(self, params):
        self.apikey=params['apikey']
        self.cal = calibration.Calibration.sharedclass
                self.docal = self.checkcal(params)

    def outputdata(self, datapoints, sampletime):
        if self.docal == 1:
            datapoints = self.cal.calibrate(datapoints)
        arr ={} 
        counter = 1
        for i in datapoints:
            if i['value'] != None: #this means it has no data to upload.
                arr['field' + str(counter)] = round(i['value'], 2)
            counter += 1
        url = "https://api.thingspeak.com/update?key=" + self.apikey
        url += "&created_at=" + sampletime.strfdatetime("%Y-%m-%dT%H:%M:%S")
        try:
            z = requests.get(url, params=arr)
            if z.text == "0": 
                print("ThingSpeak Error: " + z.text)
                print("ThingSpeak URL: " + z.url)
                return False
        except Exception:
            return False
        return True
