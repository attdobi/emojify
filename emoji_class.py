from __future__ import division,unicode_literals
import os
base_dir=os.path.expanduser('~')+'/emojify' #get home dir, point to emojify folder
import pandas as pd
import datetime
import numpy as np
from nltk.stem.snowball import SnowballStemmer
from string import punctuation
import re, collections, random, datetime
import psycopg2

#mongo query limit is currently set to 1000

# guarantee unicode string... #no need in python3 (will cause an error)
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

class emoji_lib:
	"""Emoji Class"""
	def __init__(self):
		#setup stemmer
		self.stemmer = SnowballStemmer('english')
		#connect to local postgreSQL server
		self.conn = psycopg2.connect("host=localhost port=5432 dbname=emoji_db user=postgres password=darkmatter")
		self.cur = self.conn.cursor()
		#load emoji keys for cuts, only need to do once
		self.emjDict=self.buildDict()
	def sql_word(self,word):
		word=word.lower()
		word=word.replace("'","''")#replace all apostrophes with double for SQL query
		if (re.findall("[a-z]",word) == []) or len(word.split())>1:
			return word
		else:
			return ' '+word #text is already saved with words split from emojis. potential punctuation afterwards
		
	######### Index search result, write to SQL DB ###########################
	def index_result(self, word,freq_filter,face_filter,pattern_type,user_lang,xdata,ydata):
		word=self.sql_word(word)
		word=word.replace("''","'")#undo all double apostrophes used for SQL query
		self.cur.execute("INSERT INTO emoji_search (\
		date,\
		searchTerm ,\
		emojiLabel,\
		emojiCount,\
		FreqFilter,\
		FaceFilter,\
		PatternType,\
		Lang\
		)\
		VALUES (\
		%s,%s,%s,%s,%s,%s,%s,%s\
		)",(\
		datetime.datetime.utcnow(),\
		word,\
		xdata,\
		ydata,\
		freq_filter,\
		face_filter,\
		pattern_type,\
		user_lang,\
		))
		self.conn.commit() #submit change to db
		
	def index_skin_result(self,word,user_lang,xdata,ydata):
		word=self.sql_word(word)
		word=word.replace("''","'")#undo all double apostrophes used for SQL query
		self.cur.execute("INSERT INTO emoji_skin_search (\
		date,\
		searchTerm ,\
		emojiLabel,\
		emojiCount,\
		Lang\
		)\
		VALUES (\
		%s,%s,%s,%s,%s\
		)",(\
		datetime.datetime.utcnow(),\
		word,\
		xdata,\
		ydata,\
		user_lang,\
		))
		self.conn.commit() #submit change to db
	
	######### query SQL code: ################################################
	######### query skin code: ################################################
	def emoji_skin(self, word='dog',user_lang='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
		
		self.cur.execute("SELECT Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiSkinLabel) as Label, unnest(emojiSkinCount) as Freq FROM emoji_tweet WHERE (emojiSkinCountSum>0 AND LOWER(text) LIKE '%{:s}%') {:s} ) as T group by Label order by TFreq DESC;".format(word,lang))
		result=self.cur.fetchall()
		xdata=[val[0] for val in result]
		ydata=[val[1] for val in result]
		return xdata, ydata
	####### emoji Tweet search ###################################################
	def filter_emoji(self, word='dog',face_filter='off',pattern_type='single',user_lang='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
		
		if face_filter=='off':########## If the face filter is OFF: ################
			if pattern_type=='single':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} )) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang))
			elif pattern_type=='string':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq FROM emoji_tweet WHERE (emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} )) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq FROM emoji_tweet WHERE (emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} )) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang))
			else:#return all
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} )) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as Freq, unnest(emojiLabelFaceFilter) as FF FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} )) as T WHERE(T.FF is True) group by T.Label order by TFreq DESC limit 15;".format(word,lang))
			elif pattern_type=='string':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq FROM emoji_tweet WHERE (emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq FROM emoji_tweet WHERE (emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang))
			else:#return all
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]) )) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang))
		#### Calculate and return the result #####################
		result=self.cur.fetchall()
		xdata=[val[0] for val in result]
		ydata=[val[1] for val in result]
		return xdata, ydata

	def filter_emoji_freq(self,word='dog',face_filter='off',pattern_type='single',user_lang='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
		
		if face_filter=='off':########## If the face filter is OFF: ################
			if pattern_type=='single':
				self.cur.execute("SELECT emojiLabel[1] as label,SUM(emojiCount[1]) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} ) group by label order by Freq DESC limit 15;".format(word,lang))
			elif pattern_type=='string':
				self.cur.execute("SELECT emojistrLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet WHERE(emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} ) group by label order by Freq DESC limit 10;".format(word,lang))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT emojiPatternLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet WHERE(emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} ) group by label order by Freq DESC limit 10;".format(word,lang))
			else:#return all
				self.cur.execute("SELECT Label,SUM(T.Freq) as TFreq From (SELECT unnest(ARRAY[emojiLabel[1],emojistrLabel[1],emojiPatternLabel[1]]) as Label, unnest(ARRAY[emojiCount[1],coalesce(emojistrCount[1],0),coalesce(emojiPatternCount[1],0)]) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} )) as T group by Label order by TFreq DESC limit 15;".format(word,lang))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT emojiLabel[1] as label,SUM(emojiCount[1]) as Freq FROM emoji_tweet where(emojiLabelFaceFilter[1] is true AND LOWER(text) LIKE '%{:s}%' {:s} ) group by label order by Freq DESC limit 15;".format(word,lang))
			elif pattern_type=='string':
				self.cur.execute("SELECT emojistrLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet WHERE(emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False])) group by label order by Freq DESC limit 10;".format(word,lang))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT emojiPatternLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet WHERE(emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False])) group by label order by Freq DESC limit 10;".format(word,lang))
			else:#return all
				self.cur.execute("SELECT Label,SUM(T.Freq) as TFreq From (SELECT unnest(ARRAY[emojiLabel[1],emojistrLabel[1],emojiPatternLabel[1]]) as Label, unnest(ARRAY[emojiCount[1],coalesce(emojistrCount[1],0),coalesce(emojiPatternCount[1],0)]) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]) )) as T group by Label order by TFreq DESC limit 15;".format(word,lang))
		#### Calculate and return the result #####################
		result=self.cur.fetchall()
		xdata=[val[0] for val in result]
		ydata=[val[1] for val in result]
		return xdata, ydata
	######## Search Surrounding Text ########################################################
	def filter_emoji_surr(self,word='dog',face_filter='off',pattern_type='single',user_lang='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang,lang2='',''
		else:
			lang,lang2="WHERE( lang='{:s}' )".format(user_lang), "AND lang='{:s}' ".format(user_lang)
		
		if face_filter=='off':########## If the face filter is OFF: ################
			if pattern_type=='single':
				self.cur.execute("SELECT Label,SUM(C) as Freq  from (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as C, unnest(prev_sentence) as prev, unnest(next_sentence) as next FROM emoji_tweet {:s} ) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by Freq DESC limit 15;".format(lang,word,word))
			elif pattern_type=='string':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet WHERE (emojistrTypes>0 {:s} )) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,word,word))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet WHERE (emojiPatternTypes>0 {:s} )) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,word,word))
			else:#return all
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq, unnest(array_cat(prev_sentence,array_cat(emojistr_prev_sentence,emojistr_prev_sentence))) as prev, unnest(array_cat(next_sentence,array_cat(emojistr_next_sentence,emojistr_next_sentence))) as next FROM emoji_tweet {:s}) as ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 15;".format(lang,word,word))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT Label,SUM(C) as Freq  from (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as C, unnest(emojiLabelFaceFilter) as FF, unnest(prev_sentence) as prev, unnest(next_sentence) as next FROM emoji_tweet {:s} ) ST WHERE (FF is True AND (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%')) group by Label order by Freq DESC limit 15;".format(lang,word,word))
			elif pattern_type=='string':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet WHERE (emojistrTypes>0 {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,word,word))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet WHERE (emojiPatternTypes>0 {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,word,word))
			else:#return all
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq, unnest(array_cat(prev_sentence,array_cat(emojistr_prev_sentence,emojistr_prev_sentence))) as prev, unnest(array_cat(next_sentence,array_cat(emojistr_next_sentence,emojistr_next_sentence))) as next FROM emoji_tweet WHERE (NOT(emojiLabelFaceFilter @> ARRAY[False]) {:s} )) as ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 15;".format(lang2,word,word))
		#### Calculate and return the result #####################
		result=self.cur.fetchall()
		xdata=[val[0] for val in result]
		ydata=[val[1] for val in result]
		return xdata, ydata
	########## Sample Art ##############################################################
	def sample_art(self):
		self.cur.execute("SELECT b.text from emoji_tweet a join tweet_dump b on a.tweet_id=b.id WHERE (a.emojiCountSum > 30) order by random() limit 40;")
		art=[_u(text[0]) for text in self.cur.fetchall()]
		return '\n\n'.join(art)
		
	def sample_art_options(eCount='>=30',eTypes='>=0',eStrTypes='>=0',ePatTypes='>=0',NL='>=0'):
		self.cur.execute("SELECT text from emoji_tweet WHERE (emojiCountSum {:s} AND emojiTypes {:s} AND emojistrTypes {:s} AND emojiPatternTypes {:s} AND newlineCount {:s}) order by random() limit 40;".format(eCount,eTypes,eStrTypes,ePatTypes,NL))
		
	########## emoji context code ##########################################
	def get_context(self,word,user_lang):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
			
		self.cur.execute("SELECT text from emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} ) order by random() DESC limit 1000;".format(_u(word),lang))
		result=[_u(text[0]) for text in self.cur.fetchall()]
		return '\n'.join(result)
	######### emojify code: ################################################
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
				#RETURN string must be in utf-8 format
				return _u(xdata[0]) #most frequent
		else:
			return ""
		
	def buildDict(self):
		emoji_key = pd.read_excel(base_dir+'/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
		emoji_TS = pd.read_excel(base_dir+'/data/emoji_TS.xlsx', encoding='utf-8', skiprows=1)
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
		#text=text #ensure unicode encoding
		#print(emoji.emojize(''.join([lookup(word) for word in words(text)])))
		#print(''.join([lookup(word) for word in words(text)])+'\n'+text)
		return text+'\n'+''.join([self.lookup_and_search(word,lyric=lyric) for word in self.words(text)])
		#return [lookup(word) for word in words(text)]
	
	def emojifyLyrics(self, a):
		song_list=dict({"Shake it Off (Taylor Swift)":"ShakeItOff_TS.txt","Boyz n The Hood (Eazy-E)":"Boyz-n-the-Hood.txt","Let it Snow (Frozen)":"Let-It_Go.txt","Lollipop (Lil Wayne)":"Lollipop-LW.txt"})
		try:
			TS = _u(file(base_dir+'/data/lyrics/'+song_list[a]).read())
		except KeyError:
			TS=['']
		return('\n'.join([self.emoji_fy(line,lyric=True) for line in TS.split('\n')]))
	
	def emojifyText(self, a):
		return('\n'.join([self.emoji_fy(line) for line in a.split('\n')]))