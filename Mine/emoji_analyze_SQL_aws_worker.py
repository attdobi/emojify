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
conn = psycopg2.connect("host=172.31.22.77 port=5432 dbname=emoji_db user=postgres password=darkmatter")
cur = conn.cursor()

#set up parallel cores:, we will use 3
if len(sys.argv) == 2:
	core_number=int(sys.argv[1])-1
	cores=2
	print('running on core {:d} of 2'.format(core_number+1))
else:
	#run on 1 core
	print('running on one core')
	cores=1
	core_number=0
	
#get the last timestamp from emoji_tweet table. Eventually change to select last tweet_id
#query the tweet_dump table for times greater than last emoji_tweet time
run=True
if __name__ == "__main__":
	while run:
		cur.execute("SELECT tweet_id from has_emoji WHERE MOD(tweet_id,2)=%s order by tweet_id DESC limit 1;",(core_number,))#find last processed id
		last_id=cur.fetchone()
		#last_id=15532115
		cur.execute("SELECT * from tweet_dump WHERE (id>%s AND MOD(id,2)=%s) LIMIT 10000;",(last_id,core_number)) 
		#where id>tweet_id, only odd or even
		SQL_result=cur.fetchall()
		print(len(SQL_result))
		if len(SQL_result)>0:#begin analysis
			for result in SQL_result:
				analyze_tweet_emojis(conn,cur,result)
		else:#else quit ... or sleep
			run=False