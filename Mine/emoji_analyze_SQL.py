from __future__ import division
import os
base_dir=os.path.expanduser('~')
import datetime
import time
import psycopg2
from Mine_lib import *

CONSUMER_KEY = 'JJNPMPuZubIrFIqDNARJRDPDb'
CONSUMER_SECRET = 'd6MlAqrJFcdyJac9aCQpBHPbwGs5eJB8zkTn5wA3tqBLHZgw0b'
OAUTH_TOKEN = '3229899732-piSMFy32Vi0VSyXJX8R9y2qrkr0piesoHXBdI3v'
OAUTH_TOKEN_SECRET = 'Jq9oTRMUjHRgA7NkJLLHIEyjtCRhYiFHdWkpBw28IBtHG'

#connect to postgrSQL
#conn = psycopg2.connect("host=172.31.22.77 port=5432 dbname=emoji_db user=postgres password=darkmatter")
conn = psycopg2.connect("host=192.168.1.187 port=5432 dbname=emoji_db user=postgres password=darkmatter")
cur = conn.cursor()

#set up parallel cores:, we will use 4 ### Setup number of cores to be used here ########
if len(sys.argv) == 3:
	core_number = int(sys.argv[1]) - 1
	cores = int(sys.argv[2])
	print('running on core {:d} of {:d}'.format(core_number + 1, cores))
else:
	#run on 1 core
	print('running on one core')
	cores = 1
	core_number = 0

# Get the last timestamp from emoji_tweet table. Eventually change to select last tweet_id.
# Query the tweet_dump table for times greater than last emoji_tweet time.
run = True
if __name__ == "__main__":
	while run:
		# Find last processed id
		cur.execute("SELECT tweet_id from has_emoji WHERE MOD(tweet_id, %s) = %s order by id DESC limit 1;", (cores, core_number))
		last_id=cur.fetchone()
		#last_id = 228235327
		# TODO(attila): Raspberry Pi's memory is limited to 1 GB. I manually set the query to 50,000 entries (about 2h to compute).
		cur.execute("SELECT * from tweet_dump WHERE id > %s AND MOD(id, %s) = %s ORDER BY id LIMIT 50000;", (last_id, cores, core_number)) 
		SQL_result=cur.fetchall()
		print(len(SQL_result))
		if len(SQL_result) >= 1:
			#begin analysis
			for result in SQL_result:
				analyze_tweet_emojis(conn,cur,result)
		#else quit ... or sleep
		else:
			# Exit:
			#run = False
			# Sleep:
			print 'Waiting 1 minute.'
			time.sleep(60)
		#run=False ### REMOVE THIS LINE AFTER START!!!!###