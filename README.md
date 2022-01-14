# OPC: OctoPrint Communicator
A middleware for establishing basic communication between Octoprint-connected 3D printers and various equipment.
For those simply looking for a python-based Octoprint client, there are probably better alternatives out there.

### Main idea
This program is our monument to laziness and flexibility. 
It is meant to run natively on an Omron IPC connected to industrial automation equipment, so as to save us the hardships of handling all communications using IEC 61131-3-compliant languages.
When initialized, a CSV containing Octopi instances and API keys are parsed and used to create as many client objects as there are in the list.
These clients then read and store the status of each printer, saving them to a suitable file format to be read by the IPC.

### Down the line
I will probably not develop this any further in its current state.

*Copyright © 2020 Fredrik Siem Taklo. MIT License.*
