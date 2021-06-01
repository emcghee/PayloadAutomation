#!/usr/local/bin/python3

# This tool will take an an artifact from commandline and grab IoC information such as exif and hashes and print them

# It can also be imported like a library to be used by other tools. 
# If used as a library, the items won't be printed to the console, as this is done in the Main function

import subprocess
import sys

# These shouldn't change that much, but possibly will from system to system. If so, set them here:
msbuildPath = '/usr/local/bin/msbuild'


##### Compiler Functions #####

def msbuildCSharp(file, platform="x64", config="Release", target="Rebuild"):

	# msbuild $opsPath/Persistence/$persistenceProject/$persistenceProject.sln /t:Rebuild /p:Configuration=Release,Platform=x64 > /dev/null

	flags = [file, "/t:{}".format(target), "/p:Configuration={},Platform={}".format(config, platform)]
	output = subprocess.run([msbuildPath] + flags, capture_output=True)
	return output.stdout.decode()


##### Main ########

def parseArguments():
	parser = ArgumentParser()

	parser.add_argument("-l", "--language", default="c#", 
		help="the language to compile. Currently supported: [C#,]")
	parser.add_argument("file", help="the solution, project, or source-code file to compile")

	args = parser.parse_args()
	return args


def main():
	args = parseArguments()
	print(msbuildCSharp(args.file))
	

if __name__ == '__main__':
	# There are some imports which aren't used when this is a library, so they are imported here instead
	from argparse import ArgumentParser
	main()