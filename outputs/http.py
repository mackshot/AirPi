import output
import os
import BaseHTTPServer
from datetime import datetime
import time
from threading import Thread
from string import replace
import calibration
import numpy
import re

# useful resources:
# http://unixunique.blogspot.co.uk/2011/06/simple-python-http-web-server.html
# http://docs.python.org/2/library/simplehttpserver.html
# http://docs.python.org/2/library/basehttpserver.html#BaseHTTPServer.BaseHTTPRequestHandler
# https://wiki.python.org/moin/BaseHttpServer
# http://stackoverflow.com/questions/10607621/a-simple-website-with-python-using-simplehttpserver-and-socketserver-how-to-onl
# http://www.huyng.com/posts/modifying-python-simplehttpserver/
# http://stackoverflow.com/questions/6391280/simplehttprequesthandler-override-do-get

class HTTP(output.Output):
	requiredData = ["wwwPath"]
	optionalData = ["port", "history", "title", "about", "calibration", "historySize", "historyInterval", "historyCalibrated"]

	details = """
<div class="panel panel-default">
	<div class="panel-heading">
		<h4 class="panel-title"><a class="accordion-toggle collapsed" data-toggle="collapse" data-parent="#accordion" href="#collapse-$sensorId$">
			$readingName$: $reading$ ($units$)
		</a></h4>
	</div>
	<div id="collapse-$sensorId$" class="panel-collapse collapse">
		<div class="panel-body"><p>
			Sensor: <em>$sensorName$</em><br/>
			Description: <em>$sensorText$</em>
		</p></div>
	</div>
</div>""";

	rssItem = "<item><title>$sensorName$</title><description>$reading$ $units$</description></item>\n"

	def __init__(self,data):
		self.www = data["wwwPath"]

		if "port" in data:
			self.port = int(data["port"])
		else:
			self.port = 8080

		if "history" in data:
			if data["history"].lower() in ["off","false","0","no"]:
				self.history = 0
			elif os.path.isfile(data["history"]):
				#it's a file to load, check if it exists
				self.history = 2
				self.historyFile = data["history"];
			else:
				# short-term history
				self.history = 1
		else:
			self.history = 0
		if "historySize" in data:
			self.historySize = data["historySize"]
		else:
			self.historySize = 2880
		if "historyInterval" in data:
			self.historyInterval = data["historyInterval"]
		else:
			self.historyInterval = 30
		if "historyCalibrated" in data:
			if data["historyCalibrated"].lower() in ["on","true","1","yes"]:
				self.historyCalibrated = 1
			else:
				self.historyCalibrated = 0
		else:
			self.historyCalibrated = 0

		if "title" in data:
			self.title = data["title"]
		else:
			self.title = "AirPi"

		if "about" in data:
			self.about = data["about"]
		else:
			self.about = "An AirPi weather station."

		self.cal = calibration.Calibration.sharedClass
		self.docal = calibration.calCheck(data)
		self.sensorIds = []
		self.historicData = []
		self.historicAt = 0

		self.handler = requestHandler
		self.server = httpServer(self, ("", self.port), self.handler)
		self.thread = Thread(target = self.server.serve_forever)
		self.thread.daemon = True
		self.thread.start()

		# load up history
		if self.history == 2:
			if self.historyCalibrated == 0:
				print "Loading uncalibrated history from " + self.historyFile
			else
				print "Loading calibrated history from " + self.historyFile

	def createSensorIds(self,dataPoints):
		for i in dataPoints:
			self.sensorIds.append(i["sensor"]+" "+i["name"])
		self.historicData = numpy.zeros([2, len(self.sensorIds)+1])

	def getSensorId(self,name):
		for i in range(0,len(self.sensorIds)):
			if name == self.sensorIds[i]:
				return i
		# does not exist, add it
		# (should only happen if the loaded history has different sensors)
		self.sensorIds.append(i["sensor"]+" "+i["name"])
		t = numpy.zeros([len(self.historicData), len(self.sensorIds)+1])
		t[0:self.historicAt,0:len(self.sensorIds)] = self.historicData
		self.historicData = t
		return len(self.sensorIds)-1

	def recordData(self,dataPoints):
		t = numpy.zeros(len(self.sensorIds)+1)
		t[0] = time.time()
		if self.historicData[self.historicAt-1,0] - t[0] < self.historyInterval:
			return
		for i in dataPoints:
			sid = self.getSensorId(i["sensor"]+" "+i["name"])
			if i["value"] != None:
				t[sid+1] = i["value"]
			else:
				t[sid+1] = 0
		self.historicData[self.historicAt] = t
		self.historicAt += 1

		if len(self.historicData) == self.historicAt and self.historicAt < self.historySize: #grow
			t = numpy.zeros([self.historicAt * 2, len(self.sensorIds)+1])
			t[0:self.historicAt,:] = self.historicData
			self.historicData = t
		elif self.historicAt == self.historySize: # shift the end off the array
			self.historicData[0:self.historicAt-1,:] = self.historicData[1:self.historicAt,:]
			self.historicAt -= 1

	def outputData(self,dataPoints):
		if self.docal == 1:
			dataPoints = self.cal.calibrate(dataPoints[:])
		if len(self.sensorIds) == 0:
			self.createSensorIds(dataPoints)
		self.recordData(dataPoints)

		self.data = dataPoints
		self.lastUpdate = time.strftime('%a, %d %b %Y %H:%M:%S %Z', time.localtime(time.time()))
		return True

class httpServer(BaseHTTPServer.HTTPServer):

	def __init__(self, httpoutput, server_address, RequestHandlerClass):
		self.httpoutput = httpoutput
		BaseHTTPServer.HTTPServer.__init__(self, server_address, RequestHandlerClass)


class requestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

	def do_GET(self):
		if self.path == '/' or self.path == '/index.html':
			self.path = 'index.html'
			index = 1
		else:
			index = 0
		if self.path == '/rss.xml':
			rss = 1
		else:
			rss = 0
		r = re.match('/graph_collapse-([0-9]).html', self.path)
		if r:
			graph = int(r.group(1))+1
			self.path = 'graph.html'
		else:
			graph = 0

		toread = self.server.httpoutput.www + os.sep + self.path
		if os.path.isfile(toread):
			pageFile = open(toread, 'r')
			page = pageFile.read()
			pageFile.close()
			response = 200
			lm = time.strftime('%a, %d %b %Y %H:%M:%S %Z', time.localtime(os.stat(toread).st_mtime))
		else:
			page = "quoth the raven, 404"
			response = 404
			lm = "Tue, 15 Nov 1994 12:45:26 GMT"

		# do substitutions here
		if index == 1 and response == 200:
			page = replace(page, "$title$", self.server.httpoutput.title)
			page = replace(page, "$about$", self.server.httpoutput.about)
			page = replace(page, "$time$", self.server.httpoutput.lastUpdate)
			# sort out the sensor stuff
			details = ''
			for i in self.server.httpoutput.data:
				line = replace(self.server.httpoutput.details, "$readingName$", i["name"])
				line = replace(line, "$reading$", str(round(i["value"], 2)))
				line = replace(line, "$units$", i["symbol"])
				line = replace(line, "$sensorId$", str(self.server.httpoutput.getSensorId(i["sensor"]+" "+i["name"])))
				line = replace(line, "$sensorName$", i["sensor"])
				line = replace(line, "$sensorText$", i["description"])
				details += line
			if self.server.httpoutput.history != 0:
				page = replace(page, "$graph$", """'<div class="aspect-ratio"><iframe src="graph_'+id+'.html"></iframe></div>'""")
			else:
				page = replace(page, "$graph$", "\"No history available.\"")
			page = replace(page, "$details$", details)
		elif rss == 1 and response == 200:
			page = replace(page, "$title$", self.server.httpoutput.title)
			page = replace(page, "$about$", self.server.httpoutput.about)
			page = replace(page, "$time$", self.server.httpoutput.lastUpdate)
			items = ''
			for i in self.server.httpoutput.data:
				line = replace(self.server.httpoutput.rssItem, "$sensorName$", i["name"])
				line = replace(line, "$reading$", str(i["value"]))
				line = replace(line, "$units$", i["symbol"])
				items += line
			page = replace(page, "$items$", items)
		elif graph > 0 and response == 200:
			x = self.server.httpoutput.historicData[0:self.server.httpoutput.historicAt,0]
			y = self.server.httpoutput.historicData[0:self.server.httpoutput.historicAt,graph]
			data = ''
			for index, item in enumerate(x):
				data += "[%i, %f]," % (item*1000, y[index])
			page = replace(page, "$data$", data)
				

		self.send_response(response)
		if response == 200:
			fileName, fileExtension = os.path.splitext(toread)
			if fileExtension == '.png':
				self.send_header("Content-Type", "image/png")
			elif fileExtension == '.css':
				self.send_header("Content-Type", "text/css")
			elif fileExtension == '.js':
				self.send_header("Content-Type", "application/javascript")
			elif fileExtension == '.rss':
				self.send_header("Content-Type", "application/rss+xml")
			elif fileExtension == '.ttf':
				self.send_header("Content-Type", "application/x-font-ttf")
			elif fileExtension == '.woff':
				self.send_header("Content-Type", "application/font-woff")
			else:
				self.send_header("Content-Type", "text/html")
		else:
			self.send_header("Content-Type", "text/html")
		self.send_header("Content-length", len(page)-1)
		if index == 1 or rss == 1 or graph == 1:
			lm = self.server.httpoutput.lastUpdate
		self.send_header("Last-Modified", lm)
		self.end_headers()
		if self.command != 'HEAD':
			self.wfile.write(page)
		self.wfile.close()
