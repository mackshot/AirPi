from . import output
import requests
import json
from . import calibration

class Xively(output.Output):
	requiredparams = ["APIKey","FeedID","needsinternet"]
	optionalparams = ["calibration"]

	def __init__(self, params):
		self.apikey=params['apikey']
		self.feedid=params['feedid']
		self.cal = calibration.Calibration.sharedclass
                self.docal = self.checkcal(params)

	def outputData(self, datapoints):
		if self.docal == 1:
			datapoints = self.cal.calibrate(datapoints)
		arr = []
		for i in datapoints:
			# handle GPS data
			if i['name'] == "Location":
				arr.append({"location": {"disposition": i['Disposition'], "ele": i['Altitude'], "exposure": i['Exposure'], "domain": "physical", "lat": i['Latitude'], "lon": i['Longitude']}})
			if i['value'] != None: #this means it has no data to upload.
				arr.append({"id":i['name'],"current_value":round(i['value'],2)})
		a = json.dumps({"version":"1.0.0","datastreams":arr})
		try:
			z = requests.put("https://api.xively.com/v2/feeds/"+self.feedid+".json",headers={"X-apikey":self.apikey},data=a)
			if z.text!="": 
				print("Error: Xively message - " + z.text)
				print("Error: Xively URL - " + z.url)
				return False
		except Exception:
			return False
		return True
