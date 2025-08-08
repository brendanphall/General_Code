# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# emailFilegdb.py
# ---------------------------------------------------------------------------
import sys, os
import datetime

if len(sys.argv)<2:
	print ('Usage: emailFilegdb.py [zip file]')
	sys.exit()

zipfile = sys.argv[1]

if not os.path.exists(zipfile):
	print("ERROR: File not found: " + zipfile)
	sys.exit(1)

import smtplib
# For guessing MIME type based on file name extension
import mimetypes
import email.utils
from email import encoders
from email.message import Message
#from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
#from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import calendar

currentDateTime = datetime.datetime.now().replace(microsecond=0)
print(currentDateTime)
cd_mm = currentDateTime.strftime("%m")   # this returns a leading 0 on months < 10
cd_mmm = currentDateTime.strftime("%b")  # Month name, short version
cd_dd = currentDateTime.day
cd_yyyy = currentDateTime.year

# get tracts for last month
tddays = datetime.timedelta(days=cd_dd)
yesterday = currentDateTime - tddays
mm = yesterday.strftime("%m")   # this returns a leading 0 on months < 10
mmm = yesterday.strftime("%b")  # Month name, short version
dd = yesterday.day
yyyy = yesterday.year

host = 'email-smtp.us-east-1.amazonaws.com'
port = 587
sender = 'support@hosting.jws.com'
senderName = 'Sewall Support'
replyto = 'support@jws.com'
smtp_username = 'AKIAWY6Y2H2N6GLY5XNC'
smtp_password = 'BIr2YxmIiJG+xKePxUJl6hxr1VNE/44S1npB49mlbKQp'
fromSender = "support@jws.com"
fromSenderName = "Sewall Support"

subject = f"Tract Export {mmm} {yyyy}"

# The email body for recipients with non-HTML email clients.
textbody = f"The Tract Export for {mmm} {yyyy} has been completed."

# # The HTML body of the email.
# htmlbody = "<html><head></head><body><p>The RE Metrics processing has been completed.</p></body></html>"

users = ['Joe.ClarkII@canfor.com', 'cammo@sewall.com']
# users = ['cammo@sewall.com']

for user in users:
	# Email Person to be notified
	print (user)
	recipient = user

	# Create message container
	msg = MIMEMultipart('mixed')
	msg['Subject'] = subject
	msg['From'] = email.utils.formataddr((senderName, sender))
	msg['To'] = recipient
	msg['Reply-To'] = replyto
	# Comment or delete the next line if you are not using a configuration set
	# msg.add_header('X-SES-CONFIGURATION-SET',CONFIGURATION_SET)

	# Record the MIME types of both parts - text/plain and text/html.
	part1 = MIMEText(textbody, 'plain')
	# part2 = MIMEText(htmlbody, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.
	msg.attach(part1)
	# msg.attach(part2)

	efile = open(zipfile, 'rb')
	ctype, encoding = mimetypes.guess_type(zipfile)
	maintype, subtype = ctype.split('/', 1)
	part3 = MIMEBase(maintype, subtype)
	part3.set_payload(efile.read())
	efile.close()
	encoders.encode_base64(part3)
	part3.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(zipfile))
	msg.attach(part3)

	# Try to send the message.
	try:  
		server = smtplib.SMTP(host, port)
		server.ehlo()
		server.starttls()
		# stmplib docs recommend calling ehlo() before & after starttls()
		server.ehlo()
		server.login(smtp_username, smtp_password)
		server.sendmail(sender, recipient, msg.as_string())
		server.close()
	# Display an error message if something goes wrong.
	except Exception as e:
		print ("Error: ", e)
	else:
		print ("Email sent")

