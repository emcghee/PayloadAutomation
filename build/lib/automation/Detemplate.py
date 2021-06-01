#!/usr/local/bin/python3
import secrets
import base64
import re
import sys
from importlib import import_module


# This is a local config.py file with your configuration settings
# Eventually I should move this to YAML or something... Would take a bit of a re-write based on the reflection I did
#from config import *

# Here is where I do it as a YAML file!
import yaml

class TemplateHandler:

	def __init__(self, userid="", sessiontokenname=""):
		# We create a unique userid instantiation of this object. If you want to loop to do multiple payloads (multiple targets), put the instantiation of this object in the user loop
		if userid == "":
			self.userid = secrets.token_urlsafe(10)
		else:
			self.userid = userid

		if sessiontokenname == "":
			self.sessiontokenname = "PHPSESSIONID"
		else:
			self.sessiontokenname = sessiontokenname

	def files(self, files, templatestring):

		try:
			# format should be files.exe.payload
			notusingthis, fileformat, fileskey = templatestring.split(".")
		except:
			print("Malformed files template string used: {}".format(templatestring))
		filecontents = ""

		# plaintext is a keyword that let's us know to read in the contents of the file as a string and just embed that string
		# This is useful for embedding HTML attachments into email templates
		if fileformat == "plaintext":
			try:
				with open(files.get(fileskey), "r") as file:

					filecontents = file.read()
			except:
				print("Error reading plaintext from file: {}".format(files.get(fileskey)))
				pass
		else:

			try:
				with open(files.get(fileskey), "rb") as file:

					filedata = file.read()

					filecontents = base64.b64encode(filedata).decode()
			except:
				print("Error reading from file: {}".format(files.get(fileskey)))
				pass

		return filecontents

	def links(self, links, templatestring):
		# This takes the protocol and url (from the links dict) and combines them with the linkdomain to create a complete URL for an href value
		# Note: This function uses a global called linkdomain set in the globals section of the YAML

		try:
			# format should be links.https.more-info
			notusingthis, linkprotocol, linkskey = templatestring.split(".")
		except:
			print("Malformed links template string used: {}".format(templatestring))

		linkstring = ""

		if linkprotocol == "http" or linkprotocol == "https":
			# Remember: linkdomain is a global set in the globals section of the YAML
			linkstring = linkprotocol + "://" + globalVars["linkdomain"] + links.get(linkskey) + self.sessiontokenname + "=" + self.userid
		else:
			print("Improper protocol provided. Only http or https accepted. Protocol provided: {}".format(linkprotocol))

		return linkstring


	def embededimages(self, images, templatestring):
		try:
			# format should be images.gif.logo
			notusingthis, imageformat, prependuri, imageskey = templatestring.split(".")

			dataurl = "data:image/{};base64,".format(imageformat)
		except:
			print("Malformed images template string used: {}".format(templatestring))
		filecontents = ""

		try:
			with open(images.get(imageskey), "rb") as file:
				filedata = file.read()
				filecontents = base64.b64encode(filedata).decode()

			if prependuri == "true":
				filecontents = dataurl + filecontents

		except:
			print("Error reading from image file: {}".format(images.get(imageskey)))
			print("Template string we received was: {}".format(templatestring))
			print("Images dict we have on file: {}".format(images))
			sys.exit()
			pass

		return filecontents

	def linkedimages(self, images, templatestring):
		# This takes the protocol and url (from the links dict) and combines them with the linkdomain to create a complete URL for an href value
		# Note: This function uses a global called linkdomain set in the globals section of the YAML

		try:
			# format should be links.https.more-info
			notusingthis, linkprotocol, linkskey = templatestring.split(".")
		except:
			print("Malformed links template string used: {}".format(templatestring))

		linkstring = ""

		if linkprotocol == "http" or linkprotocol == "https":
			# Remember: linkdomain is a global set in the globals section of the YAML

			linkstring = linkprotocol + "://" + globalVars["linkdomain"] + images.get(linkskey) + self.sessiontokenname + "=" + self.userid
		else:
			print("Improper protocol provided. Only http or https accepted. Protocol provided: {}".format(linkprotocol))

		return linkstring

	def trackingimages(self, images, templatestring):
		# This takes the protocol and url (from the links dict) and combines them with the linkdomain to create a complete URL for an href value
		# Note: This function uses a global called trackingdomain set in the globals section of the YAML

		try:
			# format should be links.https.more-info
			notusingthis, linkprotocol, linkskey = templatestring.split(".")
		except:
			print("Malformed links template string used: {}".format(templatestring))

		linkstring = ""

		if linkprotocol == "http" or linkprotocol == "https":
			# Remember: linkdomain is a global set in the globals section of the YAML

			linkstring = linkprotocol + "://" + globalVars["trackingdomain"] + images.get(linkskey) + self.sessiontokenname + "=" + self.userid
		else:
			print("Improper protocol provided. Only http or https accepted. Protocol provided: {}".format(linkprotocol))

		return linkstring

	def emails(self, emails, templatestring):
		# This is a simple string replacement for the email from the emails dict
		try:
			# format should be email.replay-to
			notusingthis, emailskey = templatestring.split(".")
		except:
			print("Malformed emails template string used: {}".format(templatestring))

		return emails.get(emailskey)

	def strings(self, strings, templatestring):
		# This is a simple string replacement for the string from the strings dict
		try:
			# format should be strings.file-name
			notusingthis, stringskey = templatestring.split(".")
		except:
			print("Malformed strings template string used: {}".format(templatestring))

		return strings.get(stringskey)


class MissingTemplateValue(Exception):
	"""Exception raised for errors in the input for template values.

	Attributes:
		missingvalue -- input which was missing and caused the error
		message -- explanation of the error
	"""

	def __init__(self, missingvalue):
		self.missingvalue = missingvalue
		self.message = "Template value missing: {}".format(missingvalue)

		super().__init__(self.message)

def usage():
	print("Usage:	python3 {} [config] [template] [output]".format(sys.argv[0]))



def main(config, template, output):


	# Taken from commandline args
	configFile = config
	attachmenttemplate = template
	attachmentoutputfile = output

	# Was considering doing this all together, but I think the arguments is a better approach
	emailtemplate = "SecureEmailTemplateExample.tmpl"



	# Read in the values into a settings dictionary
	with open(configFile) as file:
		settings = yaml.full_load(file)

	# Load in the globals
	global globalVars
	globalVars = settings["globals"]

	# Read in the template file where we will replace some strings
	with open(attachmenttemplate, "r") as file:
		template = file.read()

	# We are going to look for anything that starts with {% and ends with %}. Example: {%images.gif.lock%}
	attachmentregex = r"{%(.*?)%}"
	pattern = re.compile(attachmentregex)
	matches = pattern.findall(template)

	# our TemplateHandler is what does all the work
	handler = TemplateHandler()
	for match in matches:
		try:
			matchtype = match.split('.')[0]
			#print(matchtype)
		except:
			print("Match found without type: {}".format(match))
			pass

		# Checks the global variables for a variable with that name (i.e. files.exe.payload template value and files = {} variable)
		#if matchtype in globals():
		if matchtype in settings.keys():


			# Use reflection to call the right method in the TemplateHandler class. 
			# This allows us to do different actions/manipulations 
			replacement = getattr(handler, matchtype)(settings.get(matchtype), match)

			if replacement:
				template = template.replace(("{%" + match + "%}"), replacement)
			else:
				print("It looks like we are missing the replacement value for {} in your YAML file.".format(match))
				sys.exit("Go fix your shit and come back when it's right! (╯°□°)╯︵ ┻━┻")
		else:
			print("Matchtype not found: {}".format(matchtype))
			sys.exit("Go fix your shit and come back when it's right! (╯°□°)╯︵ ┻━┻")


	with open(attachmentoutputfile, "w") as file:
		file.write(template)
	print("Wrote output to: {}".format(attachmentoutputfile))

if __name__ == '__main__':

	if (len(sys.argv) != 4):
		print("Error: Incorrect number of arguments provided.\n")
		usage()
	else:
		main(sys.argv[1], sys.argv[2], sys.argv[3])
