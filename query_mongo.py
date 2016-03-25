import datetime
from pymongo import MongoClient
import pandas as pd
import numpy
import scipy
import matplotlib as mpl
import collections

client = MongoClient()
db = client.emoji_db
tweets = db.emoji_tweets


def filter_emoji(word='dog'):
	S= collections.defaultdict(lambda:0)
	for tweet in tweets.find({'text':{"$regex": word}, 'emjTypes':{'$gt':0}, 'emjCount':{'$gt':0} } ): 
		#print(tweet['text']) #print the text
		for val in tweet['emjText']:
			S[val[0]]+=val[1]
	df=pd.DataFrame([ (key,value) for key,value in S.items()], columns=('emoji','freq'))
	#df.sort_values('freq',ascending=0)
	xdata = df.sort_values('freq',ascending=0)['emoji'].values[:15] #top 20 frequency
	ydata = df.sort_values('freq',ascending=0)['freq'].values[:15] #top 20 frequency
	return xdata, ydata

def filter_emoji_freq(word='dog'):
	Sf=collections.defaultdict(lambda:0)
	for tweet in tweets.find({'text':{"$regex": word}, 'emjTypes':{'$gt':0}, 'emjCount':{'$gt':0} } ): 
		#print(tweet['mostFreqEmoji']) #print the text
		Sf[tweet['mostFreqEmoji']]+=tweet['mostFreqEmojiCount']
	df=pd.DataFrame([ (key,value) for key,value in Sf.items()], columns=('emoji','freq'))
	#dSf.sort_values('freq',ascending=0)
	xdata = df.sort_values('freq',ascending=0)['emoji'].values[:15] #top 20 frequency
	ydata = df.sort_values('freq',ascending=0)['freq'].values[:15] #top 20 frequency
	return xdata, ydata
