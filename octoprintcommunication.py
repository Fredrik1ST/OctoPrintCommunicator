import logging
import json
import requests

from requests.exceptions import ConnectionError
from requests.adapters import HTTPAdapter

'''
This class contains the necessary commands to extract information from Raspberry Pis running Octoprint,
as well as commands to start print jobs. Communication between the script and Pis are done through parsing of
JSON objects. Methods primarily return JSON-formatted strings.
'''

class OctoPrintClient:

    def __init__(self, ipAddress, apiKey, username, password, path_log='Log.txt'):
        '''
        Initialize a "client". Each client handles one connection to one printer.
        A logger object is initialized to write error logs as well.
        '''
        self.ipAddress = ipAddress
        self.apiKey = apiKey
        self.username = username
        self.password = password

        logging.basicConfig(filename=path_log, level=logging.ERROR,
                            format='%(asctime)s %(levelname)s %(name)s %(message)s')
        self.logger = logging.getLogger(__name__)


    def get(self, url, headers=None, timeout=1):
        '''
        Performs a HTTP get using the Requests library.
        Handles some common exceptions.
        Returns a Requests response object.
        '''
        try:
            return requests.get(url, headers=headers, timeout=timeout)
        except ConnectionError as e:
            #print("ERROR: Pi is not connected!")
            print(self.logger.error("Cannot connect to Raspberry Pi"))
            self.logger.error(e)


    def post(self, url, headers=None, data=None, json=None, timeout=1):
        '''
        Performs a HTTP post using the Requests library.
        Handles some common exceptions.
        Returns a Requests response object.
        '''
        try:
            return requests.post(url, headers=headers, data=data, json=json, timeout=timeout)
        except ConnectionError as e:
            self.logger.error("Cannot connect to Raspberry Pi")
            self.logger.error(e)


    def printDebugInfo(self):
        '''
        Print relevant info about this object for debugging purposes
        '''
        print("IP: " + self.ipAddress + ", ")
        print("API key: " + self.apiKey + ", ")
        print("Username: " + self.username + ", ")
        print("Password: " + self.password + ", ")


    def login(self):
        '''
        Log into Octoprint on the specified IP address
        Returns response as string.
        '''
        url = "http://" + self.ipAddress + "/api/login"
        json = {"user": self.username, "pass": self.password}
        r = self.post(url, json=json)
        if r is not None:
            return r.text
        else:
            self.logger.error(str(self.ipAddress) + " Login response: No connection to Pi")


    def logout(self):
        '''
        Log out from Octoprint on the specified IP address.
        You probably do not need to use this for this program.
        Returns response as string.
        '''
        url = "http://" + self.ipAddress + "/api/logout"
        r = self.post(url)
        if r is not None:
            return r.text
        else:
            self.logger.error(str(self.ipAddress) + " Logout response: No connection to Pi")


    def connectToPrinter(self):
        '''
        Connect to the 3D printer over USB. Default values are used.
        Returns response code as integer.
        Note that establishing connection may take several seconds.
        TODO: Seems to return HTTP 204 no matter what. Investigate.
        '''
        url = "http://" + self.ipAddress + "/api/connection"
        headers = {"Content-Type": "application/json", "X-Api-Key": self.apiKey}
        json = {"command": "connect"}
        r = self.post(url, headers=headers, json=json)
        if r is not None:
            return r.status_code
        else:
            self.logger.error(str(self.ipAddress) + " ConnectToPrinter response: No connection to Pi")


    def disconnectFromPrinter(self):
        '''
        Disconnect from the 3D printer if connected.
        Returns response as string.
        '''
        url = "http://" + self.ipAddress + "/api/connection"
        headers = {"Content-Type": "application/json", "X-Api-Key": self.apiKey}
        json = {"command": "disconnect"}
        r = self.post(url, headers=headers, json=json)
        if r is not None:
            return r.status_code
        else:
            self.logger.error(str(self.ipAddress) + " DisconnectFromPrinter response: No connection to Pi")


    def isPrinterConnected(self):
        '''
        Check if the specified Pi is connected to the Printer.
        Returns: True if connected, False if not, None if Pi cannot be reached
        '''
        url = "http://" + self.ipAddress + "/api/connection"
        headers = {"X-Api-Key": self.apiKey}

        r = self.get(url, headers=headers)
        if r is not None:
            rJson = json.loads(r.text)

            if (rJson["current"]["state"]) == "Operational": # Can be Closed or Operational
                    return True
            else:
                    return False
        else:
            self.logger.error(str(self.ipAddress) + " isPrinterConnected response: No connection to Pi")


    def getPrinterStatus(self):
        '''
        Request the current status of the connected 3D printer.
        Returns the response (JSON object) as a string.
        '''
        url = "http://" + self.ipAddress + "/api/printer"
        headers = {"X-Api-Key": self.apiKey}
        print("Accessing " + url + " using API Key " + self.apiKey)

        r = self.get(url, headers=headers)
        if r is not None:
            rJson = json.loads(r.text)
            if r.text == "Printer is not operational":
                self.logger.error(print("Printer " + self.ipAddress + " is not operational"))
            else:
                return r.text
        else:
            self.logger.error(str(self.ipAddress) + " getPrinterStatus response: No connection to Pi")


    def getCurrentPrintJob(self):
        '''
        Check to see what is currently printing, if anything at all.
        Return JSON string containing job info.
        '''
        url = "http://" + self.ipAddress + "/api/job"
        headers = {"X-Api-Key": self.apiKey}
        r = self.get(url, headers=headers)
        if r is not None:
            return r.text
        else:
            self.logger.error(str(self.ipAddress) + " getCurrentPrintJob response: No connection to Pi")


    def selectPrintJob(self, gcodePath):
        '''
        Select gcode stored on the Pi.
        Argument: path to the gcode
        Returns the response as JSON string
        '''
        url = "http://" + self.ipAddress + gcodePath
        headers = {"Content-Type": "application/json", "X-Api-Key": self.apiKey}
        json = {"command": "select"}
        r = self.post(url, headers=headers, json=json)
        if r is not None:
            return r.text


    def startPrintJob(self):
        '''
        Tell the specified printer to start printing the selected G-code
        G-code should be uploaded to the Manulab-folder in octoprint in advance.
        Arguments: Octopi IP address, Octopi API key, path to g-code file on the pi
        Returns: response as JSON string
        '''
        url = "http://" + self.ipAddress + "/api/job"
        headers = {"Content-Type": "application/json", "X-Api-Key": self.apiKey}
        json = {"command": "start"}
        r = self.post(url, headers=headers, json=json)
        if r is not None:
            return r.text
        else:
            if self.isPrinterConnected():
                self.logger.error(str(self.ipAddress) + " startPrintJob response: "
                                                      + "Could not start print job. Printer might be busy")
            else:
                self.logger.error(str(self.ipAddress) + " startPrintJob response: "
                                                      + " Could not start print job. No connection to Pi")