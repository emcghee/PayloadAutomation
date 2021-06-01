#!/usr/local/bin/python3

# This tool will take an an artifact from commandline and grab IoC information such as exif and hashes and print them

# It can also be imported like a library to be used by other tools. 
# If used as a library, the items won't be printed to the console, as this is done in the Main function

from magic import from_file
import hashlib

# For now, I am using subprocess to run exiftool, which I installed through Brew. 
# Might eventually look into other python libraries for this

import subprocess
import sys

# These shouldn't change that much, but possibly will from system to system. If so, set them here:
exifToolPath = '/usr/local/bin/exiftool'
touchPath = '/usr/bin/touch'

########### EXIF #############
def getFileType(file):
	return from_file(file, mime=True)


def getExif(file):
	# We check the file type and see if we have pre-built some flags for that specific file type (i.e. Exe)
	filetype = getFileType(file)
	#print(filetype)
	exifOutput = None

	if filetype == 'application/x-dosexec':
		exifOutput = getExifEXE(file)
	elif filetype == 'application/pdf':
		# I still need to figure out what's relevant on a PDF, for now, you just get the basic exif.
		exifOutput = getExifOther(file)
	elif filetype == 'text/plain':
		# It's a plaintext file so all it would show is the date
		pass
	else:
		exifOutput = getExifOther(file)
		
	return exifOutput

def getExifEXE(file, flags = ["-productname", "-productversion", "-assemblyversion", "-comments", "-companyname", "-filedescription", "-fileversionnumber", "-productversionnumber", "-filemodifydate", "-fileaccessdate", "-fileinodechangedate"]):
	# Useful information for an EXE file
	
	exifData = subprocess.run([exifToolPath] + flags + [file], capture_output=True)
	return exifData.stdout.decode()

def getExifOther(file):
	# Run it without limiting with flags
	exifData = subprocess.run([exifToolPath] + [file], capture_output=True)
	return exifData.stdout.decode()

def timestomp(file, timestamp="201512180130.09"):
	# touch -a -m -t $timestompdate $exepathPersist
	touchflags = ["-a", "-m", "-t"]
	result = subprocess.run([touchPath] + touchflags + [timestamp] + [file], capture_output=True)

	# Let's double check that our timestomp worked
	exifdateflags = ["-filemodifydate", "-fileaccessdate",  "-fileinodechangedate"]
	exifData = subprocess.run([exifToolPath] + exifdateflags + [file], capture_output=True)
	return exifData.stdout.decode()

######## Hashes ########

# returns a list of the hashes in the order of the hashtypes
def getHashes(file, hashtypes=['md5', 'sha1', 'sha256']):
	hashlist = list()
	for hashtype in hashtypes:
		try:
			hasher = hashlib.new(hashtype)
			with open(file, 'rb') as afile:
				buf = afile.read()
				hasher.update(buf)
			hashlist.append(hasher.hexdigest())
		except:
			print("Issue hashing, maybe you provided an incorrect hashtype")
			hashlist.append(None)

	return hashlist

##### Main ########

def parseArguments():
	parser = ArgumentParser()

	parser.add_argument("-t", "--timestomp", help="a datetime to stomp the file to, example \"201512180130.09\"")
	parser.add_argument("file", help="the file to check")

	args = parser.parse_args()
	return args


def main():
	args = parseArguments()
	
	print(getExif(args.file))

	# Defaults return MD5, SHA1, SHA256
	# Print that nicely
	print(getHashes(args.file))
	if args.timestomp:
		print(timestomp(args.file, args.timestomp))

if __name__ == '__main__':
	# There are some imports which aren't used when this is a library, so they are imported here instead
	from argparse import ArgumentParser
	main()