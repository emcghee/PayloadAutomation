#!/usr/local/bin/python3
from argparse import ArgumentParser
from ntpath import basename

from payload_automation.striker import CSConnector
from payload_automation.artifactor import getHashes, timestomp

# alias iocs="python3 <PATH>/PayloadAutomation/examples/IoCs.py"

def main(args):
	teamserver = args.teamserver
	files = args.files
	java = args.java

	for artifact in files:
		with CSConnector(cs_host=teamserver, cs_directory=java) as cs:
			md5, sha1, sha256 = getHashes(artifact)
			filename = basename(artifact)
			
			cs.logToEventLog(f"Indicator of Compromise: {filename} - MD5: {md5}")
			cs.logToEventLog(f"Indicator of Compromise: {filename} - SHA1: {sha1}")
			cs.logToEventLog(f"Indicator of Compromise: {filename} - SHA256: {sha256}")


def parseArguments():
	parser = ArgumentParser()
	parser.add_argument('teamserver', help='The teamserver to post IOCs to.')
	parser.add_argument('files', nargs='+', help='The files to post IOCs of.')
	parser.add_argument('-j', metavar='java', dest='java', default='/Applications/Cobalt Strike 4/Cobalt Strike 4.1.app/Contents/Java', help='The path to the cobalt strike java directory. Default is /Applications/Cobalt Strike 4/Cobalt Strike 4.1.app/Contents/Java')
	
	args = parser.parse_args()

	return args


if __name__ == "__main__":
	args = parseArguments()
	main(args)
