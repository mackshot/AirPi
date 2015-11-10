"""A module to write AirPi data to a MySQL database.

A module to write AirPi data to a MySQL database. The database must include
fields named exactly the same as each sensor "name". Values recorded in the
database do not have any units associated with them. There is no facility
to include GPS data at this time.
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
        statement = "INSERT INTO obs (`Station`, `Sample_Time`"
        for point in datapoints:
            if point["name"] == "Location":
                print("No provision for GPS data in sqlDatabase plugin at this time")
            else:
                statement += ", `" + point["name"] + "`"
                statement += ", `" + point["name"] + "_units`"
        statement += ") VALUES (\"" + self.params["station"] + "\", \"" + str(sampletime) + "\""
        for point in datapoints:
            statement += ", " + str(point["value"])
            statement += ", \"" + point["unit"] + "\""
        statement += ");"
        #print(statement)
        curs.execute(statement)
        if curs.rowcount == 0:
            print("I might have failed to save the data!")
        conn.commit()
        conn.close()
        return True
