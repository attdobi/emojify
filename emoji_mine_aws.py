import json
import tweepy
from tweepy.streaming import StreamListener
#from twitter import Twitter, OAuth, TwitterHTTPError, TwitterStream, auth
import pandas as pd
import re, collections
import numpy as np
CONSUMER_KEY = 'JJNPMPuZubIrFIqDNARJRDPDb'
CONSUMER_SECRET = 'd6MlAqrJFcdyJac9aCQpBHPbwGs5eJB8zkTn5wA3tqBLHZgw0b'
OAUTH_TOKEN = '3229899732-piSMFy32Vi0VSyXJX8R9y2qrkr0piesoHXBdI3v'
OAUTH_TOKEN_SECRET = 'Jq9oTRMUjHRgA7NkJLLHIEyjtCRhYiFHdWkpBw28IBtHG'

import os
base_dir=os.path.expanduser('~')

import datetime
import time
from pymongo import MongoClient
#setup mongo DB
client = MongoClient()
db = client.emoji_db
collection = db.emoji_tweets

#read emoji codes:
emoji_key = pd.read_excel(base_dir+'/emojify/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" if sum([c=="*" for c in code])==0]

def get_keys(tweet):
    max_index=0
    max_count=len(tweet['statuses'][max_index].keys())
    
    for ii in range(len(tweet['statuses'])):
        if max_count < len(tweet['statuses'][ii].keys()):
            max_index=ii
            
    return tweet['statuses'][max_index].keys()

def print_tweets_w_emj(T_DF,num=0):
    for item in T_DF['text'][T_DF['emjSum']>=num]:
        print(item)
        
def make_twitter_DF(tweet): #create PD dataframe
    columns=get_keys(tweet)
    for ii in range(len(tweet['statuses'])): 
        diff= list(set(columns)-set(tweet['statuses'][ii].keys()))
        for val in diff:
            tweet['statuses'][ii][val]=""
    return pd.DataFrame([tweet['statuses'][ii] for ii in range(len(tweet['statuses']))], columns=get_keys(tweet)) 

def Search_Word(q):
    # Initiate the connection to Twitter REST API
    twitter = Twitter(auth=OAuth( OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY,  CONSUMER_SECRET))       
    tweet= twitter.search.tweets(q=q,lang='en', result_type='recent',count=200)
    T_DF=make_twitter_DF(tweet)
    
    #long search function, more than 100
    #T_DF=long_search(twitter,q,300)
    
    T_DF['emjText']=[[(emcode, len(re.findall(emcode,T_DF['text'][ii]))) for emcode in emj_codes\
                      if (len(re.findall(emcode,T_DF['text'][ii])) > 0)] for ii in range(len(T_DF))]
    T_DF['emjSum']=[sum([item[1] for item in T_DF['emjText'][ii]]) for ii in range(len(T_DF))]
    T_DF['emjTypes']=[len(T_DF['emjText'][ii]) for ii in range(len(T_DF))]
    T_DF['searchWordSum']=[len(re.findall(q,T_DF['text'][ii].lower())) for ii in range(len(T_DF))]
    return T_DF

def Analyze_Freq(T_DF,emj_per_tweet=1,rep_emj_per_tweet=1, emj_types_per_tweet=1, nword=0):
    DFcut=T_DF[(T_DF['emjSum']>=emj_per_tweet) & (T_DF['searchWordSum']>=nword) \
               & (T_DF['emjTypes']>=emj_types_per_tweet)] 
    
    S=dict()
    for key, value in sum(DFcut['emjText'],[]):
        if value>=rep_emj_per_tweet:
            try:
                S[key] +=value
            except KeyError:
                S[key]=value
        
    return pd.DataFrame([(key,S[key]) for key in S],columns=('emoji','freq'))

def count_words(text):
    S = collections.defaultdict(lambda:0)
    for word in text.split():
        S[word.lower()]+=1
    return max(S, key=S.get), S[max(S, key=S.get)]
    
    
class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    '''
    def on_data(self, data):
        if  'in_reply_to_status' in data:
            self.on_status(data)
        elif 'delete' in data:
            delete = json.loads(data)['delete']['status']
            if self.on_delete(delete['id'], delete['user_id']) is False:
                return False
        elif 'limit' in data:
            if self.on_limit(json.loads(data)['limit']['track']) is False:
                return False
        elif 'warning' in data:
            warning = json.loads(data)['warnings']
            print warning['message']
            return false
    '''
    #Action is here, mine_for_emojis
    def on_status(self, status):
        mine_for_emojis(status)
        return True
    #error handling
    def on_delete(self, status_id, user_id):
        #print( str(status_id) + "\n")
        return
    def on_limit(self, track):
        #print(track + "\n")
        return
    def on_error(self, status):
        return False
    def on_timeout(self):
        print("Timeout, sleeping for 60 seconds...\n")
        time.sleep(60)
        return 
        
    
def mine_for_emojis(tweet):
    emjText=[(emcode, len(re.findall(emcode,tweet.text))) for emcode in emj_codes\
                      if (len(re.findall(emcode,tweet.text)) > 0)]

    if len(emjText) >0:

        emjCount=sum([item[1] for item in emjText])
        emjTypes = len(emjText)
        a=np.array(emjText)
        mostFreqEmoji = a[np.argsort(a[:, 1])][-1][0]
        mostFreqEmojiCount = int(a[np.argsort(a[:, 1])][-1][1])
        mostFreqWord, mostFreqWordCount = count_words(tweet.text)

        entry = {"date": datetime.datetime.utcnow(),\
            "created_at": tweet.created_at,\
        "text": tweet.text,\
        "retweet_count": tweet.retweet_count,\
     "favorite_count": tweet.favorite_count,\
     "lang": tweet.lang,\
     "goe": tweet.geo,\
     "coordinates": tweet.coordinates,\
     "emjText": emjText, "emjCount": emjCount, "emjTypes": emjTypes, "mostFreqEmoji": mostFreqEmoji,\
     "mostFreqEmojiCount": mostFreqEmojiCount, "mostFreqWord": mostFreqWord,\
     "mostFreqWordCount": mostFreqWordCount}

        collection.insert_one(entry).inserted_id

        print(tweet.text)
		
if __name__ == "__main__":
	l=StdOutListener()
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
	api = tweepy.API(auth)
	myStream = tweepy.Stream(auth = api.auth, listener=l)
	myStream.sample()
