from __future__ import division
import os
base_dir=os.path.expanduser('~')
import datetime
import time
import tweepy
from tweepy.streaming import StreamListener
import psycopg2
from Mine_lib import *

CONSUMER_KEY = 'JJNPMPuZubIrFIqDNARJRDPDb'
CONSUMER_SECRET = 'd6MlAqrJFcdyJac9aCQpBHPbwGs5eJB8zkTn5wA3tqBLHZgw0b'
OAUTH_TOKEN = '3229899732-piSMFy32Vi0VSyXJX8R9y2qrkr0piesoHXBdI3v'
OAUTH_TOKEN_SECRET = 'Jq9oTRMUjHRgA7NkJLLHIEyjtCRhYiFHdWkpBw28IBtHG'

#connect to postgrSQL
conn = psycopg2.connect("host=localhost port=5432 dbname=emoji_db user=postgres password=darkmatter")
cur = conn.cursor()

class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    #Mine=MineEmojis()
    def on_status(self, status):
        mine_tweets(conn,cur,status)
        return True
    def on_error(self, status):
        print(status)
        
if __name__ == "__main__":
	l=StdOutListener()
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
	api = tweepy.API(auth)
	myStream = tweepy.Stream(auth = api.auth, listener=l)
	myStream.sample()
