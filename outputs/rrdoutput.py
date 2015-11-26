"""Output AirPi data to an RRD file.

Output AirPi data to a Round-Robin Database (RRD) file
(http://oss.oetiker.ch/rrdtool/). RRD does require some setup by the
user beforehand; this is outside the remit of this module - only basic
RRD support is provided, with minimal error checking. This module
assumes that 'rrdtool' and 'python-rrdtool' are both installed on your
system.

The RRD database should be created in the shell first: an example would
be something along the lines of:

rrdtool create /home/pi/`hostname`.rrd --step 5 \
DS:Temperature-BMP:GAUGE:10:U:U \
DS:Pressure:GAUGE:10:U:U \
DS:Relative_Humidity:GAUGE:10:U:U \
DS:Temperature-DHT:GAUGE:10:U:U \
DS:Light_Level:GAUGE:10:U:U \
DS:Nitrogen_Dioxide:GAUGE:10:U:U \
DS:Carbon_Monoxide:GAUGE:10:U:U \
DS:Air_Quality:GAUGE:10:U:U \
DS:Volume:GAUGE:10:U:U \
RRA:AVERAGE:0.9:1:34560 \
RRA:AVERAGE:0.9:1:105120

Note the last two lines, indicating that two sets of records will be
maintained:
* for a record every  5 seconds during 2 days = 2*24*60*12 =  34560
* for an average over 5 minutes during 1 year =  365*24*12 = 105120

Remember that the Round-Robin nature of RRD means that when the max.
counter is reached for each record set, older values will be
over-written.

To output a graph of results, you may want to use something like the
following in your shell:

rrdtool graph 'graph.png' \
    --imgformat 'PNG' \
    --title "AirPi Output" \
    --watermark "N.B. Some values may be too small to show on graph." \
    --vertical-label "Value" \
    --width '1000' \
    --height '800' \
    --start now-6000s \
    --end now-5920s \
    'DEF:Temp-BMP=file.rrd:Temp-BMP:AVERAGE' \
    'DEF:Pressure=file.rrd:Pressure:AVERAGE' \
    'DEF:Hum=file.rrd:Relative_Humidity:AVERAGE' \
    'DEF:Temp-DHT=file.rrd:Temp-DHT:AVERAGE' \
    'DEF:Light=file.rrd:Light_Level:AVERAGE' \
    'DEF:NO2=file.rrd:Nitrogen_Dioxide:AVERAGE' \
    'DEF:CO=file.rrd:Carbon_Monoxide:AVERAGE' \
    'DEF:AQ=file.rrd:Air_Quality:AVERAGE' \
    'DEF:Vol=file.rrd:Volume:AVERAGE' \
    'LINE1:Temp-BMP#0099CC:Temperature-BMP (C))' \
    'LINE1:Pressure#0099CC:Pressure (hPa)' \
    'LINE1:Hum#993399:Relative Humidity (%)' \
    'LINE1:Temp-DHT#0099CC:Temperature-DHT (C))' \
    'LINE1:Light#66FF33:Light (Ohms)' \
    'LINE1:NO2#3366CC:Nitrogen Dioxide (Ohms)' \
    'LINE1:CO#FF9966:Carbon Monoxide (Ohms)' \
    'LINE1:AQ#CC33FF:Air Quality / VOCs (Ohms)' \
    'LINE1:Vol#999966:Volume (Ohms)'

This module is based on code by Francois Guillier, with permission
(http://www.guillier.org/blog/2014/08/airpi/).

"""


import output
import datetime
import time
import rrdtool

class RRDOutput(output.Output):
    """A module to output AirPi data to an RRD file.

    A module which is used to output data from an AirPi into a
    RRD file. This can include GPS data if
    present, along with metadata (again, if present).

    """

    requiredSpecificParams = ["outputDir", "outputFile"]

    def __init__(self, config):
        super(RRDOutput, self).__init__(config)
        # open the file persistently for append
        self.filename = self.params["outputDir"] + "/" + self.params["outputFile"]
        self.file = open(self.filename, "a")

    def output_data(self, datapoints, sampletime):
        """Output data.

        Output data in the format stipulated by the plugin. Calibration
        is carried out first if required.
        Note this method takes account of the different data formats for
        'standard' sensors as distinct from the GPS. The former present
        a dict containing one value and associated properties such as
        units and symbols, while the latter presents a dict containing
        several readings such as latitude, longitude and altitude, but
        no units or symbols.

        Args:
            self: self.
            datapoints: A dict containing the data to be output.
            sampletime: datetime representing the time the sample was taken.

        Returns:
            boolean True if data successfully written to file.

        """
        if self.params["calibration"]:
            datapoints = self.cal.calibrate(datapoints)
        names = []
        data = [str(int(time.time()))]
        for point in datapoints:
            if point["name"] != "Location":
                names.append(point["name"].replace(' ', '_'))
                data.append(str(point["value"]))
        #print("Data to be written is:")
        #print(':'.join(names), ":".join(data))
        try:
            print("[" + time.strftime("%H:%M:%S") + "] Writing to RRD file...")
            rrdtool.update(self.filename, '-t', ':'.join(names), ":".join(data))
            print(time.strftime("[%H:%M:%S]") + " ... RRD file written.")
        except Exception as theexception:
            print(str(theexception))
        return True
