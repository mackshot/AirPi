import output
import datetime
import time
import calibration
import socket

class CSVOutput(output.Output):
	requiredParams = ["outputFile"]
	optionalParams = ["calibration"]

	def __init__(self, params):
		if "<date>" in params["outputFile"]:
                        filenamedate = time.strftime("%Y%m%d-%H%M")
                        params["outputFile"] = params["outputFile"].replace("<date>", filenamedate)
 		if "<hostname>" in params["outputFile"]:
                        if socket.gethostname().find('.')>=0:
                                filenamehost = socket.gethostname()
                        else:
                                filenamehost = socket.gethostbyaddr(socket.gethostname())[0]
                	params["outputFile"] = params["outputFile"].replace("<hostname>", filenamehost)
		# open the file persistently for append
		self.file = open(params["outputFile"], "a")
		# write a header line so we know which sensor is which?
		self.header = False;
		self.cal = calibration.Calibration.sharedClass
                self.docal = self.checkCal(params)

	def outputData(self,dataPoints):
		if self.docal == 1:
			dataPoints = self.cal.calibrate(dataPoints)

		line = "\"" + str(datetime.datetime.now()) + "\"," + str(time.time())
		if self.header == False:
			header = "\"Date and time\",\"Unix time\"";

		for i in dataPoints:
			if self.header == False:
				header = "%s,\"%s %s (%s) (%s)\"" % (header, i["sensor"], i["name"], i["symbol"], i["readingType"])
			line = line + "," + str(i["value"])

		# if it's the first write of this instance do a header so we know what's what
		if self.header == False:
			self.file.write(header + "\n")
			self.header = True
		# write the data line to the file
		self.file.write(line + "\n")
		# don't forget to flush the file in case of power failure
		self.file.flush()
		return True

	#need an exit hook to close the file nicely
	def __del__(self):
		self.file.flush()
		self.file.close()
