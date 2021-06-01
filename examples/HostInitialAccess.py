#!/usr/local/bin/python3

from Striker import CSConnector
from Artifactor import getHashes

iafile = "/Users/nameless/Desktop/SafeSpectre.txt"
md5, sha1, sha256 = getHashes(file=iafile, hashtypes=["md5", "sha1","sha256"])
with CSConnector(
	cs_host="127.0.0.1", 
	cs_user="Fautline", 
	cs_directory="/Applications/Cobalt Strike 4.0/Cobalt Strike 4.0.app/Contents/Java") as cs:
		cs.hostPlainFile(file_path=iafile,
		 uri="/SafeSpectre.txt",
		 port=443,
		 use_ssl=True,
		 description="Initial Access - Stage 1 - MD5:{},SHA1:{},SHA256:{}".format(md5, sha1, sha256))