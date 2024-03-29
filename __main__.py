from octoprintcommunication import OctoPrintClient
from threading import Timer
from pathlib import Path
from time import sleep
import configparser
import logging
import pandas
import json
import csv

'''
In this module, a list of IP addresses and API keys for Octoprint-connected 3D printers are read, then used to create 
instances of OctoPrintCommunicator clients. The main program then handles communication between printer OPC clients 
and various equipment.
'''


# First we need to set up the necessary variables to make the script run.
# Settings and file paths are read from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

opcs = list()                                                   # For storing all initialized OctoPrintClient objects
path_ListOfPrinters = Path(config['Paths']['ListOfPrinters'])   # Path to the list of printer IPs / API keys
path_PrinterCommands = Path(config['Paths']['PrinterCommands']) # Path to printer commands from the IPC
path_Log = Path(config['Paths']['Log'])                         # Where to write the error log
verbose = config['Settings'].getboolean('Verbose')            # Toggle whether or not to print all responses to console

# Set up logger
logging.basicConfig(
    filename=path_Log, level=logging.ERROR, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


def importPrinterList():
    '''
    Import Octopi / printer IP addresses and API keys from the local ListOfPrinters.csv
    Usernames and passwords for the Octoprint user on each Pi is included as well.
    Lists are read by parsing columns. The first row should contain the following fields:
        "ipAddress", "apiKey", "username", "password". The delimiter sign is automatically inferred (, or ;).
    All valid rows are used to create OctoPrintClient objects, which are then stored in a list.
    '''
    global ipList
    global apiList
    global usernameList
    global passwordList
    try:
        # Check for Excel delimiter info in the file. If it's there, use it.
        with open(path_ListOfPrinters, 'r') as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                delimiter = dialect.delimiter
                header = 0

        # Read csv to Pandas dataframe using first row as headers
        dataframe = pandas.read_csv(path_ListOfPrinters, sep=delimiter, header=header)
        ipList = list(dataframe.ipAddress)
        apiList = list(dataframe.apiKey)
        usernameList = list(dataframe.username)
        passwordList = list(dataframe.password)

        # Create an OPC instance for every element in the List Of Printers
        for i in range(len(ipList)):
            opcs.append(OctoPrintClient(ipList[i], apiList[i], usernameList[i], passwordList[i]))

    except Exception as e:
        logger.error(e)
        logger.error(print("ListOfPrinters.csv may be missing or of invalid format"))

def connectToPrinters():
    '''
    Autoconnect the Pis to their respective printers (over USB)

    '''
    for i, opc in enumerate(opcs):
        if not opc.isPrinterConnected:
            response = opc.connectToPrinter()
            print("HTTP " + str(response))

def updatePrinterStatus():
    '''
    Read status from all available printers. Write each printer's status as a row in a CSV file.
    Also, for testing purposes, write each printer's status to a separate txt file.
    '''

    # Row structure: [IP]; [connected]; [printing] ; [ready] ; [operational] ; [pausing] ; [paused] ; [finishing] ; [nozzle temp] ; [bed temp]
    opcStatusFields = ("IP;Connected;Printing;Ready;Operational;Pausing;Paused;Finishing;NozzleTemp;BedTemp\n")

    # Set up status CSV & txt
    path_statusCsv = Path("PrinterStatus/PrinterStatus.csv")
    statusCsv = open(path_statusCsv, 'w+') # Clear file before writing
    statusCsv.write(opcStatusFields)

    # Create status string for each connected printer
    for i, opc in enumerate(opcs):
        printerIsConnected = opc.isPrinterConnected()
        if printerIsConnected:
            opcStatus = opc.getPrinterStatus()
            opcSJ = json.loads(opcStatus)
            # Row structure: [IP]; [connected]; [printing] ; [ready] ; [operational] ; [pausing] ; [paused] ; [finishing] ; [nozzle temp] ; [bed temp]
            opcStatusString =   (
                                str(opc.ipAddress) + ";" +
                                str(printerIsConnected) + ";" +
                                str(opcSJ['state']['flags']['printing']) + ';' +
                                str(opcSJ['state']['flags']['ready'])    + ';' +
                                str(opcSJ['state']['flags']['operational']) + ';' +
                                str(opcSJ['state']['flags']['pausing'])  + ';' +
                                str(opcSJ['state']['flags']['paused'])   + ';' +
                                str(opcSJ['state']['flags']['finishing']) + ";" +
                                str(opcSJ['temperature']['bed']['actual']) + ';' +
                                str(opcSJ['temperature']['tool0']['actual'])
                                )
        else:
            opcStatus = "Not connected to Pi!"
            opcStatusString =   (
                                str(opc.ipAddress) + ";" +
                                str(printerIsConnected) + ";" +
                                ';' +
                                ';' +
                                ';' +
                                ';' +
                                ';' +
                                ";" +
                                ';'
                                )
        # Append status string to CSV & txt
        statusCsv.write(opcStatusString + "\n")
        path_statusTxt = Path("PrinterStatus/" + "printer" + str(i) + ".txt")
        with open(path_statusTxt, 'w+') as statusTextFile:
            statusTextFile.write(opcStatusFields + opcStatusString)

        # Print responses if the verbose debugging variable is set to true
        if verbose:
            print(opc.ipAddress + " printer status: " + opcStatus)

    # Close CSV to avoid access issues
    statusCsv.close()

def getCommandList():
    '''
    Read and sort CSV containing commands for the printer. The CSV is intended to be written by an IPC.
    Returns the commands as lists of IP addresses, commands and arguments.
    '''

    # Check for Excel delimiter info in the file. If it's there, use it.
    with open(path_PrinterCommands, 'r') as csvfile:
        csvData = csv.reader(csvfile)
        csvDataList = list(csvData)
        if verbose:
            print("First row in command CSV: ", str(csvDataList[0][0]))
        if csvDataList[0][0] == "sep=;":
            delimiter = ";"
            header = 1
        elif csvDataList[0][0] == "sep=,":
            delimiter = ","
            header = 1
        # If there's no delimiter info in the CSV, infer it automatically.
        else:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            delimiter = dialect.delimiter
            header = 0

    # Read csv to Pandas dataframe using the first relevant row as headers
    dataframe = pandas.read_csv(path_PrinterCommands, sep=delimiter, header=header)
    ipList = list(dataframe.IP_Address)
    commandList = list(dataframe.Command)
    argumentList = list(dataframe.Argument)

    # Create a 2D list of command data.
    outputList = [ipList, commandList, argumentList]

    #open(path_printerCommands, 'w').close() # Clear file after parsing it

    return outputList



'''
MAIN SCRIPT STARTS HERE
'''
if __name__ == "__main__":

    importPrinterList() # Must be run first. Otherwise there won't be any OPCs to work with.
    connectToPrinters()
    sleep(10) # Sleep for some seconds to make sure that printers get time to connect.

    updatePrinterStatus()

    commandList = getCommandList()

    # Parse and run commands
    for i, opc in enumerate(opcs):
        if opc.isPrinterConnected:
            if commandList[0][i] == opc.ipAddress:
                if commandList[1][i] == "print":

                    opc.selectPrintJob(commandList[2][i])
                    opc.startPrintJob()