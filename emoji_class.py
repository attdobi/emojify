from __future__ import division
import pandas as pd
import numpy as np
from nltk.stem.snowball import SnowballStemmer
from string import punctuation
import re, collections, random, datetime
from pymongo import MongoClient

#mongo query limit is currently set to 1000

# guarantee unicode string
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

class emoji_lib:
	"""Emoji Class"""
	def __init__(self):
		#setup stemmer
		self.stemmer = SnowballStemmer('english')
		#connect to mongo client
		client = MongoClient()
		db = client.emoji_db
		self.tweets = db.emoji_tweets
		#load emoji keys for cuts, only need to do once
		self.emjDict=self.buildDict()
		emoji_key = pd.read_excel('data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1) #this is a local variable
		self.emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
		face_index=range(69)
		self.emj_codes_face=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in face_index]
		
	#query mongo db code:
	def filter_emoji(self, word='dog',face_filter='off'):
		if face_filter=='on':
			face_filter=True
		else:
			face_filter=False
		S= collections.defaultdict(lambda:0)
		for tweet in self.tweets.find({'text':{"$regex": word}, 'emjTypes':{'$gt':0}, 'emjCount':{'$gt':0} } ).limit(1000): 
			if face_filter:
				for val in tweet['emjText']:
					if val[0] not in (self.emj_codes_face + self.emj_codes_skin):
						S[val[0]]+=val[1]
			else:
				for val in tweet['emjText']:
					if val[0] not in  self.emj_codes_skin:
						S[val[0]]+=val[1]
		df=pd.DataFrame([ (key,value) for key,value in S.items()], columns=('emoji','freq'))
		xdata = df.sort_values('freq',ascending=0)['emoji'].values[:15] #top 15 frequency
		ydata = df.sort_values('freq',ascending=0)['freq'].values[:15] #top 15 frequency
		return xdata, ydata

	def filter_emoji_freq(self,word='dog',face_filter='off'):
		if face_filter=='on':
			face_filter=True
		else:
			face_filter=False
			
		Sf=collections.defaultdict(lambda:0)
		for tweet in self.tweets.find({'text':{"$regex": word}, 'emjTypes':{'$gt':0}, 'emjCount':{'$gt':0} } ).limit(1000): 
			#print(tweet['mostFreqEmoji']) #print the text
			if face_filter:
				if tweet['mostFreqEmoji'] not in (self.emj_codes_face + self.emj_codes_skin):
					Sf[tweet['mostFreqEmoji']]+=tweet['mostFreqEmojiCount']
			else:
				if tweet['mostFreqEmoji'] not in self.emj_codes_skin:
					Sf[tweet['mostFreqEmoji']]+=tweet['mostFreqEmojiCount']
		df=pd.DataFrame([ (key,value) for key,value in Sf.items()], columns=('emoji','freq'))
		xdata = df.sort_values('freq',ascending=0)['emoji'].values[:15] #top 15 frequency
		ydata = df.sort_values('freq',ascending=0)['freq'].values[:15] #top 15 frequency
		return xdata, ydata

	def sample_art(self):
		art=[]
		for tweet in self.tweets.find({'emjCount': {"$gt": 30} ,'emjTypes': {"$gt": 0} } ):
			art.append(tweet['text'])
		random.shuffle(art)
		return '\n\n'.join(art[:40])
		
	def words(self,text):
		try:
			text=text.replace('"',"'") #remove quotes, make single quotes
		except AttributeError:
			text=text
		try:
			text=re.sub(r"\s?([^\w\s'/\-\+$]+)\s?", r" \1 ", text) #find punctuation
		except TypeError:
			text = ''
		try:
			return re.findall("[\S]+", text.lower()) #[a-z]
			#return text.lower().split()
		except AttributeError:
			return ['']
		
	def str_stemmer(self, s):
		return [self.stemmer.stem(word) for word in s]

	def lookup(self, word):
		try:
			#return ':'+self.emjDict2[self.stemmer.stem(word)]+':'
			#return self.emjDict[self.stemmer.stem(word)]
			return self.emjDict[word]
		except KeyError:
			return ""

	def lookup_and_search(self, word,lyric):
		if word in self.emjDict:
			return self.emjDict[word]
		elif lyric==False:
			xdata,ydata=self.filter_emoji(word=word,face_filter='on')
			if len(xdata)==0:
				return ""
			else:
				return xdata[0] #most frequent
		else:
			return ""
		
	def buildDict(self):
		emoji_key = pd.read_excel('data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
		emoji_TS = pd.read_excel('data/emoji_TS.xlsx', encoding='utf-8', skiprows=1)
		emoji_TS=emoji_TS.replace(np.nan,"") # need to remove nan
		emjDict=dict()
		for key, name, annotation,action in zip(emoji_key['Unicode'], emoji_key['Name'], emoji_key['Annotations'], emoji_key['Action']):
			for stem_word in self.str_stemmer(self.words(annotation)+self.words(action)):
			#for stem_word in words(annotation)+words(action):
				emjDict[_u(stem_word)]=key
		for word, val in zip(emoji_TS['word'], emoji_TS['emoji']):
			for stem_word in self.words(word):
				emjDict[_u(stem_word)]=val
		return emjDict
	
	def emoji_fy(self,text,lyric=False):
		text=_u(text) #ensure unicode encoding
		#print(emoji.emojize(''.join([lookup(word) for word in words(text)])))
		#print(''.join([lookup(word) for word in words(text)])+'\n'+text)
		return text+'\n'+''.join([self.lookup_and_search(word,lyric=lyric) for word in self.words(text)])
		#return [lookup(word) for word in words(text)]
	
	def emojifyLyrics(self, a):
		song_list=dict({"Shake it Off (Taylor Swift)":"ShakeItOff_TS.txt","Boyz n The Hood (Eazy-E)":"Boyz-n-the-Hood.txt","Let it Snow (Frozen)":"Let-It_Go.txt","Lollipop (Lil Wayne)":"Lollipop-LW.txt"})
		try:
			TS = file("data/lyrics/"+song_list[a]).read()
		except KeyError:
			TS=['']
		return('\n'.join([self.emoji_fy(line,lyric=True) for line in TS.split('\n')]).encode('utf-8'))
	
	def emojifyText(self, a):
		return('\n'.join([self.emoji_fy(line) for line in a.split('\n')]).encode('utf-8'))