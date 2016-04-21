from __future__ import division
import os, sys
base_dir=os.path.expanduser('~')
sys.path.append(base_dir+'/emojify')
sys.path.append(base_dir+'/emojify/Mine')
from Mongo2SQL_lib import *

#connect to Mongo
client = MongoClient('172.31.22.77',27017)
db = client.emoji_db
tweets = db.emoji_tweets

#connect to postgrSQL
conn = psycopg2.connect("host=172.31.22.77 port=5432 dbname=emoji_db user=postgres password=darkmatter")
cur = conn.cursor()
    
#set up parallel cores:, we will use 3
if len(sys.argv) == 2:
	core_number=int(sys.argv[1])-1
	cores=3
	print('running on core {:d} of 3'.format(core_number))
else:
	#run on 1 core
	print('running on one core')
	cores=1
	core_number=0

#run script parallelized on 3 cores
#core numbers range from 0,1,2
    
if __name__ == "__main__":
	for tweet in tweets.find(no_cursor_timeout=True)[5858586:]:
		if (ii%cores==core_number):
			mine_tweets(tweet,Mongo=True)

