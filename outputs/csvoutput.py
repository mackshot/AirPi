from . import output
import datetime
import time
from . import calibration

class CSVOutput(output.Output):
	requiredparams = ["outputdir", "outputfile"]
	optionalparams = ["calibration", "metadata"]

	def __init__(self, params):
		if "<date>" in params['outputfile']:
                        filenamedate = time.strftime("%Y%m%d-%H%M")
                        params['outputfile'] = params['outputfile'].replace("<date>", filenamedate)
 		if "<hostname>" in params['outputfile']:
                	params['outputfile'] = params['outputfile'].replace("<hostname>", self.getHostname())
		# open the file persistently for append
		filename = params['outputdir'] + "/" + params['outputfile']
                self.file = open(filename, "a")
		# write a header line so we know which sensor is which?
		self.header = False;
		self.cal = calibration.Calibration.sharedclass
                self.docal = self.checkcal(params)

        def outputMetadata(self):
                self.metadata = self.getmetadata()
                metadata  = "\"Run started\",\"" + self.metadata['starttime'] + "\"\n"
                metadata += "\"Operator\",\"" + self.metadata['operator'] + "\"\n"
                metadata += "\"Raspberry Pi name\",\"" + self.metadata['piname'] + "\"\n"
                metadata += "\"Raspberry Pi ID\",\"" +  self.metadata['piid'] + "\""
                self.file.write(metadata + "\n")

	def outputData(self, datapoints):
		if self.docal == 1:
			datapoints = self.cal.calibrate(datapoints)

		line = "\"" + str(datetime.datetime.now()) + "\"," + str(time.time())
		if self.header == False:
			header = "\"Date and time\",\"Unix time\"";

		for i in datapoints:
			if self.header == False:
				header = "%s,\"%s %s (%s) (%s)\"" % (header, i['sensor'], i['name'], i['symbol'], i['readingType'])
			line = line + "," + str(i['value'])

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
