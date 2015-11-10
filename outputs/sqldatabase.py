"""A module to write AirPi data to a MySQL database.

A module to write AirPi data to a MySQL database. The database must include
fields with the following names and types:
Station       VARCHAR(20)
Sample_Time   DATETIME
Sensor        VARCHAR(25)
Value         DOUBLE
Unit          VARCHAR(25)
There is no facility to include GPS data at this time.
"""

import output
import MySQLdb

class sqlDatabase(output.Output):
    """A module to write AirPi data to a MySQL database.

    A module which is used to output data from an AirPi into a MySql database.

    """
    optionalSpecificParams = ["station"]
    requiredSpecificParams = ["host", "db", "user", "passwd"]

    def __init__(self, config):
        super(sqlDatabase, self).__init__(config)
        if not self.params["station"]:
            self.params["station"] = "MyAirPi"

    def output_data(self, datapoints, sampletime):
        """Output data.

        Output data in the format stipulated by the plugin. Calibration
        is carried out first if required.
        Note that no provision is made for GPS data at this time.

        Args:
            self: self.
            datapoints: A dict containing the data to be output.
            sampletime: datetime representing the time the sample was taken.

        Returns:
            boolean True if data successfully printed to stdout.

        """
        if self.params["calibration"]:
            datapoints = self.cal.calibrate(datapoints)
        conn = MySQLdb.connect(host=self.params["host"],db=self.params["db"],user=self.params["user"],passwd=self.params["passwd"])
        curs = conn.cursor()
        statement = "INSERT INTO obs (`Station`, `Sample_Time`, `Sensor`, `Value`, `Unit`) VALUES "
        for point in datapoints:
            if point["name"] != "Location":
                statement += "(\"" + self.params["station"] + "\", \"" + str(sampletime) + "\", \"" + point["name"] + "\", " + str(point["value"]) + ", \"" + point["unit"] + "\")"
            else:
                print("No provision for GPS data in sqlDatabase plugin at this time")
            if len(datapoints) > 1:
                statement += ","
        statement = statement[:-1]
        statement += ";"
        #print(statement)
        curs.execute(statement)
        if curs.rowcount == 0:
            print("I might have failed to save the data!")
        conn.commit()
        conn.close()
        return True
