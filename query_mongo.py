import datetime
from pymongo import MongoClient
import pandas as pd
import numpy
import collections

client = MongoClient()
db = client.emoji_db
tweets = db.emoji_tweets

#read emoji codes:
emoji_key = pd.read_excel('data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" \
           if (code not in emj_codes_skin) if sum([c=="*" for c in code])==0]
#remove common face emojis
noise_index=range(69)
emj_codes_face=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in noise_index]

#Functions here:
def filter_emoji(word='dog',face_filter='off'):
	if face_filter=='on':
		face_filter=True
	else:
		face_filter=False
	
	S= collections.defaultdict(lambda:0)
	for tweet in tweets.find({'text':{"$regex": word}, 'emjTypes':{'$gt':0}, 'emjCount':{'$gt':0} } ): 
		#print(tweet['text']) #print the text
		if face_filter:
			for val in tweet['emjText']:
				if val[0] not in emj_codes_face:
					S[val[0]]+=val[1]
		else:
			for val in tweet['emjText']:
				S[val[0]]+=val[1]
	df=pd.DataFrame([ (key,value) for key,value in S.items()], columns=('emoji','freq'))
	xdata = df.sort_values('freq',ascending=0)['emoji'].values[:15] #top 15 frequency
	ydata = df.sort_values('freq',ascending=0)['freq'].values[:15] #top 15 frequency
	return xdata, ydata

def filter_emoji_freq(word='dog',face_filter='off'):
	if face_filter=='on':
		face_filter=True
	else:
		face_filter=False
		
	Sf=collections.defaultdict(lambda:0)
	for tweet in tweets.find({'text':{"$regex": word}, 'emjTypes':{'$gt':0}, 'emjCount':{'$gt':0} } ): 
		#print(tweet['mostFreqEmoji']) #print the text
		if face_filter:
			if tweet['mostFreqEmoji'] not in emj_codes_face:
				Sf[tweet['mostFreqEmoji']]+=tweet['mostFreqEmojiCount']
		else:
			if tweet['mostFreqEmoji']:
				Sf[tweet['mostFreqEmoji']]+=tweet['mostFreqEmojiCount']
	df=pd.DataFrame([ (key,value) for key,value in Sf.items()], columns=('emoji','freq'))
	xdata = df.sort_values('freq',ascending=0)['emoji'].values[:15] #top 15 frequency
	ydata = df.sort_values('freq',ascending=0)['freq'].values[:15] #top 15 frequency
	return xdata, ydata
