import datetime
import pandas as pd
import numpy as np
import collections

#connect to Mongo client
from pymongo import MongoClient
client = MongoClient()
db = client.emoji_db
tweets = db.emoji_tweets

#Functions here:
def filter_emoji(emj_codes_face,emj_codes_skin,word='dog',face_filter='off'):
	if face_filter=='on':
		face_filter=True
	else:
		face_filter=False
	
	S= collections.defaultdict(lambda:0)
	for tweet in tweets.find({'text':{"$regex": word}, 'emjTypes':{'$gt':0}, 'emjCount':{'$gt':0} } ): 
		#print(tweet['text']) #print the text
		if face_filter:
			for val in tweet['emjText']:
				if val[0] not in (emj_codes_face + emj_codes_skin):
					S[val[0]]+=val[1]
		else:
			for val in tweet['emjText']:
				if val[0] not in  emj_codes_skin:
					S[val[0]]+=val[1]
	df=pd.DataFrame([ (key,value) for key,value in S.items()], columns=('emoji','freq'))
	xdata = df.sort_values('freq',ascending=0)['emoji'].values[:15] #top 15 frequency
	ydata = df.sort_values('freq',ascending=0)['freq'].values[:15] #top 15 frequency
	return xdata, ydata

def filter_emoji_freq(emj_codes_face,emj_codes_skin,word='dog',face_filter='off'):
	if face_filter=='on':
		face_filter=True
	else:
		face_filter=False
		
	Sf=collections.defaultdict(lambda:0)
	for tweet in tweets.find({'text':{"$regex": word}, 'emjTypes':{'$gt':0}, 'emjCount':{'$gt':0} } ): 
		#print(tweet['mostFreqEmoji']) #print the text
		if face_filter:
			if tweet['mostFreqEmoji'] not in (emj_codes_face + emj_codes_skin):
				Sf[tweet['mostFreqEmoji']]+=tweet['mostFreqEmojiCount']
		else:
			if tweet['mostFreqEmoji'] not in emj_codes_skin:
				Sf[tweet['mostFreqEmoji']]+=tweet['mostFreqEmojiCount']
	df=pd.DataFrame([ (key,value) for key,value in Sf.items()], columns=('emoji','freq'))
	xdata = df.sort_values('freq',ascending=0)['emoji'].values[:15] #top 15 frequency
	ydata = df.sort_values('freq',ascending=0)['freq'].values[:15] #top 15 frequency
	return xdata, ydata
