from . import output
import os
import BaseHTTPServer
from datetime import datetime
import time
from threading import Thread
from string import replace
from . import calibration
import numpy
import re
import csv

# useful resources:
# http://unixunique.blogspot.co.uk/2011/06/simple-python-http-web-server.html
# http://docs.python.org/2/library/simplehttpserver.html
# http://docs.python.org/2/library/basehttpserver.html#BaseHTTPServer.BaseHTTPRequestHandler
# https://wiki.python.org/moin/BaseHttpServer
# http://stackoverflow.com/questions/10607621/a-simple-website-with-python-using-simplehttpserver-and-socketserver-how-to-onl
# http://www.huyng.com/posts/modifying-python-simplehttpserver/
# http://stackoverflow.com/questions/6391280/simplehttprequesthandler-override-do-get
# http://bytes.com/topic/python/answers/158332-persistent-xmlrpc-connection

class HTTP(output.Output):
	requiredparams = ["wwwPath"]
	optionalparams = ["port", "history", "title", "about", "calibration", "historysize", "historyinterval", "historycalibrated", "httpversion"]

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
</div>"""


	def __init__(self, params):
		self.www = params['wwwPath']

		if "port" in params:
			self.port = int(params['port'])
		else:
			self.port = 8080

		if "history" in params:
			if params['history'].lower() in ["off", "false", "0", "no"]:
				self.history = 0
			elif os.path.isfile(params['history']):
				#it's a file to load, check if it exists
				self.history = 2
				self.historyfile = params['history'];
			else:
				# short-term history
				self.history = 1
		else:
			self.history = 0
		if "historysize" in params:
			self.historysize = int(params['historysize'])
		else:
			self.historysize = 2880
		if "historyinterval" in params:
			self.historyinterval = int(params['historyinterval'])
		else:
			self.historyinterval = 30
		if "historycalibrated" in params:
			if params['historycalibrated'].lower() in ['on","true","1","yes']:
				self.historycalibrated = 1
				self.cal = calibration.Calibration.sharedclass
			else:
				self.historycalibrated = 0
				self.cal = []
		else:
			self.historycalibrated = 0

        hostname = self.gethostname()

		if "title" in params:
			if "<hostname>" in params['title']:
                self.title = params['title'].replace("<hostname>", hostname)
  			else:
				self.title = params['title']
		else:
			self.title = "AirPi"

		if "about" in params:
            if "<hostname>" in params['about']:
 	        self.about = params['about'].replace("<hostname>", hostname)
 		else:
			self.about = params['about']
		else:
			self.about = "An AirPi weather station."

		self.cal = calibration.Calibration.sharedclass
		self.docal = self.checkcal(params)
        self.sensorids = []
		self.readingtypes = dict()
		self.historicdata = []
		self.historicat = 0
		self.temphistory = []
		self.temphistoryat = 0

		self.handler = requestHandler
		if "httpversion" in params and params['httpversion'] == "1.1":
			self.handler.protocol_version = "HTTP/1.1"
		# else it's automatically 1.0
		self.server = httpServer(self, ("", self.port), self.handler)
		self.thread = Thread(target = self.server.serve_forever)
		self.thread.daemon = True
		self.thread.start()

		# load up history
		if self.history == 2:
			if self.historycalibrated == 0:
				print("Loading uncalibrated history from " + self.historyfile)
			else:
				print("Loading calibrated history from " + self.historyfile)
			self.loaddata()

	def createsensorids(self, datapoints):
		for i in datapoints:
			self.sensorids.append(i['sensor']+" "+i['name'])
			self.readingtypes[len(self.sensorids)-1] = i['readingType']
		self.historicdata = numpy.zeros([2, len(self.sensorids)+1])
		self.temphistory = numpy.zeros([2, len(self.sensorids)])

	def loaddata(self):
		with open(self.historyfile, "r") as csvfile:
			# get file length
			for flen, l in enumerate(csvfile):
				pass
			# assume 5 second interval
			start = flen - (self.historyinterval / 5) * self.historysize
			csvfile.seek(0)

			reader = csv.reader(csvfile)
			data = []
			at = -1
			for row in reader:
				at += 1
				if at > 0 and at < start:
					continue
				# Date & Time, Unix Time, then sensors
				try:
					t = [w.replace('None', '0') for w in row[1:]]
					d = numpy.array(map(float, t))
					now = d[0]
					d = d[1:]
					for i, val in enumerate(d):
						data[i]['value'] = val
					if self.historycalibrated == 0:
						datapoints = self.cal.calibrate(data)
					else:
						datapoints = data
					self.recorddata(data, now)
				except ValueError:
					row = row[2:]
					data = []
					for i in row:
						sensor = {}
						r = re.match('([a-zA-Z0-9_-]*) ([a-zA-Z0-9_-]*) \(([a-zA-Z%_-]*)\) \(([a-zA-Z]*)\)', i)
						if r == None:
							print row
						sensor['sensor'] = r.group(1)
						sensor['name'] = r.group(2)
						sensor['symbol'] = r.group(3)
						sensor['readingType'] = r.group(4)
						data.append(sensor)
					if len(self.historicdata) == 0:
						self.createsensorids(data)
					else:
						for i in data:
							name = i['sensor']+" "+i['name']
							self.getsensorid(name)

	def getsensorid(self, name):
		for i in range(0,len(self.sensorids)):
			if name == self.sensorids[i]:
				return i
		# does not exist, add it
		return self.addsensorid(name)

	def addsensorid(self, name):
		# (should only happen if the loaded history has different sensors)
		self.sensorids.append(name)
		t = numpy.zeros([len(self.historicdata), len(self.sensorids) + 1])
		t[0:self.historicat,0:len(self.sensorids)] = self.historicdata
		self.historicdata = t
		self.temphistory = numpy.zeros([2, len(self.sensorids)])
		return len(self.sensorids) - 1

	def recorddata(self, datapoints, now=0):
		t = numpy.zeros(len(self.sensorids) + 1)
		if now == 0:
			t[0] = time.time()
		else:
			t[0] = now

		for i in datapoints:
			sid = self.getsensorid(i['sensor']+" "+i['name'])
			if i['value'] != None:
				t[sid+1] = i['value']
			else:
				t[sid+1] = 0
			self.readingtypes[sid] = i['readingType'] 

		# put the readings into temporary history for averaging
		self.temphistory[self.temphistoryat] = t[1:]
		self.temphistoryat += 1
		if len(self.temphistory) == self.temphistoryat:
			t2 = numpy.zeros([self.temphistoryat * 2, len(self.sensorids)])
			t2[0:self.temphistoryat,:] = self.temphistory
			self.temphistory = t2

		# go no further if we're not saving
		if (t[0] - self.historicdata[self.historicat-1,0]) < self.historyinterval:
			return

		# take average reading etc
		for i, r in enumerate(self.temphistory[0]):
			if self.readingtypes[i] == "sample":
				t[i+1] = numpy.mean(self.temphistory[:self.temphistoryat,i])
			elif self.readingtypes[i] == "pulseCount":
				t[i+1] = numpy.sum(self.temphistory[:self.temphistoryat,i])
		self.temphistoryat = 0 #reset

		self.historicdata[self.historicat] = t
		self.historicat += 1

		if len(self.historicdata) == self.historicat and self.historicat < self.historysize: #grow
			t = numpy.zeros([self.historicat * 2, len(self.sensorids)+1])
			t[0:self.historicat,:] = self.historicdata
			self.historicdata = t
		elif self.historicat == self.historysize: # shift the end off the array
			self.historicdata[0:self.historicat-1,:] = self.historicdata[1:self.historicat,:]
			self.historicat -= 1

	def outputdata(self, datapoints):
		if self.docal == 1:
			datapoints = self.cal.calibrate(datapoints[:])
		if len(self.sensorids) == 0:
			self.createsensorids(datapoints)
		self.recorddata(datapoints)

		self.data = datapoints
		self.lastupdate = time.strftime('%a, %d %b %Y %H:%M:%S %Z', time.localtime(time.time()))
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
			page = replace(page, "$time$", self.server.httpoutput.lastupdate)
			# sort out the sensor stuff
			details = ''
			for i in self.server.httpoutput.data:
				line = replace(self.server.httpoutput.details, "$readingName$", i['name'])
				if i['value'] != None:
					line = replace(line, "$reading$", str(round(i['value'], 2)))
				else:
					line = replace(line, "$reading$", 'None')
				line = replace(line, "$units$", i['symbol'])
				line = replace(line, "$sensorId$", str(self.server.httpoutput.getsensorid(i['sensor']+" "+i['name'])))
				line = replace(line, "$sensorName$", i['sensor'])
				line = replace(line, "$sensorText$", i['description'])
				details += line
			if self.server.httpoutput.history != 0:
				page = replace(page, "$graph$", """'<div class="aspect-ratio"><iframe src="graph_'+id+'.html"></iframe></div>'""")
			else:
				page = replace(page, "$graph$", "\"No history available.\"")
			page = replace(page, "$details$", details)
		elif rss == 1 and response == 200:
			page = replace(page, "$title$", self.server.httpoutput.title)
			page = replace(page, "$about$", self.server.httpoutput.about)
			page = replace(page, "$time$", self.server.httpoutput.lastupdate)
			items = ''
			for i in self.server.httpoutput.data:
				line = replace(self.server.httpoutput.rssitem, "$sensorName$", i['name'])
				if i['value'] != None:
					line = replace(line, "$reading$", str(round(i['value'], 2)))
				else:
					line = replace(line, "$reading$", 'None')
				line = replace(line, "$units$", i['symbol'])
				items += line
			page = replace(page, "$items$", items)
		elif graph > 0 and response == 200 and self.server.httpoutput.history != 0:
			x = self.server.httpoutput.historicdata[0:self.server.httpoutput.historicat,0]
			y = self.server.httpoutput.historicdata[0:self.server.httpoutput.historicat,graph]
			if self.server.httpoutput.readingtypes[graph-1] == "pulseCount":
				y = numpy.cumsum(y)
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
		self.send_header("Content-length", str(len(page)-1))
		if index == 1 or rss == 1 or graph == 1:
			lm = self.server.httpoutput.lastupdate
		self.send_header("Last-Modified", lm)
		self.end_headers()
		if self.command != 'HEAD':
			self.wfile.write(page)

		if self.protocol_version == "HTTP/1.1":
			self.wfile.flush()
			if self.close_connection:
				self.connection.shutdown(1)
		else:
			self.wfile.close()
