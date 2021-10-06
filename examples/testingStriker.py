#!/usr/local/bin/python3
from payload_automation.striker import CSConnector
from payload_automation.artifactor import getExif, getHashes, timestomp


with CSConnector(
	cs_host="car4.osas.red", 
	cs_user="mrx", 
	cs_directory="/Applications/Cobalt Strike 4/Cobalt Strike 4.4.app/Contents/Java"
) as cs:
		print(cs.test())
