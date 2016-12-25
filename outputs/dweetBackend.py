import pycurl
import datetime
import json

class Dweet():
    def __init__(self, data):
	self.data = data

    def send(self):

	j = json.dumps(self.data)

	c = pycurl.Curl()
	c.setopt(c.URL, "https://dweet.io:443/dweet/for/mackshot-weather")
	c.setopt(c.HTTPHEADER, ["Content-Type: application/json"])
	c.setopt(c.POSTFIELDS, j)
	c.setopt(c.WRITEFUNCTION, lambda x: None)
	c.setopt(c.VERBOSE, 0)
	c.perform()

	if (c.getinfo(c.HTTP_CODE) == 200):
    	    print("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] Successfully dweeted.")
	    return True
        else:
            print("ERROR: Did not dweet successfully.")
            print(url)
            print(data)
            print("ERROR: " + str(e))
            return False


#d = Dweet({'Dust-Level': 0.76, 'Bucket_tips': 0.0, 'Relative_Humidity': 62.2, 'Lux-TSL2561': 70.76, 'Temperature-BMP': 21.6, 'Rotations': 0.0, 'Air_Quality': 0.1, 'UVI-SI1145': 0.02, 'Volume': 11.61, 'Pressure': 1024.98, 'WindDirection': 332.1, 'Temperature-DHT': 21.0})
#d.send()