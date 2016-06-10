#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division,unicode_literals
import os
base_dir=os.path.expanduser('~') #get home dir
import pandas as pd
import datetime
import numpy as np
from nltk.stem.snowball import SnowballStemmer
from string import punctuation
import re, collections, random, datetime
import psycopg2
import json
from gensim import corpora, models, similarities

# guarantee unicode string... #no need in python3 (will cause an error)
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

class TallLabs_lib:
	"""Tall Labs Class"""
	def __init__(self):
		#setup
		self.conn = psycopg2.connect("host=localhost port=5432 dbname=amazon user=postgres password=darkmatter")
		self.cur = self.conn.cursor()
		self.QmodelB=models.Word2Vec.load(base_dir+'/models/QmodelB')
		
	def clean_result(self,model_result):
		return [item[0] for item in model_result],[item[1] for item in model_result]
		#topn=15
	def visual(self,word):
		#print(type(self.QmodelB))
		word=word.lower()
		results,counts=self.clean_result(self.QmodelB.most_similar(word,topn=5))
		source_target=[]
		for result_word in results:
			#append source target, and search next layer
			source_target.append((word,result_word,1))
			results2,counts2=self.clean_result(self.QmodelB.most_similar(result_word,topn=5))
			for result_word2 in results2:
				source_target.append((result_word,result_word2,2))
				results3,counts3=self.clean_result(self.QmodelB.most_similar(result_word2,topn=5))
				for result_word3 in results3:
					source_target.append((result_word2,result_word3,3))
		return [{"source":src,"target":tar,"group":grp} for src,tar,grp in source_target]
		
	def tree(self, word):
		word=word.lower()
		results,counts=self.clean_result(self.QmodelB.most_similar(word))
		target=[]
		child_list=[]
		for result_word in results:
			target_child=[]
			target.append(result_word)
			results2,counts2=self.clean_result(self.QmodelB.most_similar(result_word))
			for result_word2 in results2:
				target_child.append(result_word2)
			child_list.append(target_child)
		return {"name":word,"children":[{"name":tar,"children":[{"name":child,"size":3} for child in child_l] }\
		 for tar,child_l in zip(target,child_list)]}
		 
	def train(self,input):
		self.cur.execute("SELECT qa_id from training order by id DESC limit 1;")
		last_id=self.cur.fetchall()
		self.cur.execute("SELECT id,question,questiontype from qa where id>%s limit 2;",last_id)
		result=self.cur.fetchall()
		qa_id=result[0][0]
		sentence=result[0][1]
		sentence2=result[1][1] #display this one if the current one is processed
		qestion_type=result[0][2]
		
		if input != 'start':
			self.cur.execute("SELECT data_corr_yn,data_corr_oe,human_corr_yn,human_corr_oe,count_yn,count_oe from training order by id DESC limit 1;")
			result=self.cur.fetchall()[0]
			data_corr_yn=result[0]
			data_corr_oe=result[1]
			human_corr_yn=result[2]
			human_corr_oe=result[3]
			count_yn=result[4]
			count_oe=result[5]
			#check if sentence is in bag of words
			bag_of_words_yn='is,will,wil,may,might,does,dose,doe,dos,do,can,could,must,shuold,are,would,do,did'.split(',')
			if sentence.split()[0].lower() in bag_of_words_yn:
				qestion_type_bow='yes/no'
			else:
				qestion_type_bow='open-ended'
			
			if (input == 'yes/no') & (qestion_type_bow =='yes/no'):
				human_corr_yn= (human_corr_yn*count_yn+1)/(count_yn+1)
			if (input == 'yes/no') & (qestion_type_bow !='yes/no'):
				human_corr_yn= (human_corr_yn*count_yn+0)/(count_yn+1)
			if (input == 'open-ended') & (qestion_type_bow =='open-ended'):
				human_corr_oe= (human_corr_oe*count_oe+1)/(count_oe+1)
			if (input == 'open-ended') & (qestion_type_bow !='open-ended'):
				human_corr_oe= (human_corr_oe*count_oe+0)/(count_oe+1)
				
			if (input == 'yes/no') & (qestion_type =='yes/no'):
				data_corr_yn= (data_corr_yn*count_yn+1)/(count_yn+1)
			if (input == 'yes/no') & (qestion_type !='yes/no'):
				data_corr_yn= (data_corr_yn*count_yn+0)/(count_yn+1)
			if (input == 'open-ended') & (qestion_type =='open-ended'):
				data_corr_oe= (data_corr_oe*count_oe+1)/(count_oe+1)
			if (input == 'open-ended') & (qestion_type !='open-ended'):
				data_corr_oe= (data_corr_oe*count_oe+0)/(count_oe+1)
			
				
			if (input == 'open-ended'):
				count_oe=count_oe+1
			if (input == 'yes/no'):
				count_yn=count_yn+1
			self.insert_result(sentence,qestion_type,qestion_type_bow,input,qa_id,data_corr_yn,data_corr_oe,human_corr_yn,human_corr_oe,count_yn,count_oe)
			sentence=sentence2 #return the next one to display
		return(sentence)
		 
	def train_plot(self):
		self.cur.execute("SELECT * from training order by id DESC limit 1;")
		result=self.cur.fetchall()[0]
		print(result)
		yn=[result[6],result[8]]
		oe=[result[7],result[9]]
		label=['Data','BoW']
		key=['Yes/No','Open Ended']
		#print(xx,yy,key)
		return [{"values":[{"y":yn[0]*100,"x":label[0]},{"y":yn[1]*100,"x":label[1]}],"key":key[0],"yAxis":"1"},\
 {"values":[{"y":oe[0]*100,"x":label[0]},{"y":oe[1]*100,"x":label[1]}],"key":key[1],"yAxis":"1"}]
 
 	def insert_result(self,question,qestion_type,qestion_type_bow,qestion_type_human,qa_id,data_corr_yn,data_corr_oe,human_corr_yn,human_corr_oe,count_yn,count_oe):
		self.cur.execute("INSERT INTO training (\
		question,\
		qestion_type,\
		qestion_type_bow,\
		qestion_type_human,\
		qa_id,\
		data_corr_yn,\
		data_corr_oe,\
		human_corr_yn,\
		human_corr_oe,\
		count_yn,\
		count_oe\
		)\
		VALUES (\
		%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\
		)",(\
		question,\
		qestion_type,\
		qestion_type_bow,\
		qestion_type_human,\
		qa_id,\
		data_corr_yn,\
		data_corr_oe,\
		human_corr_yn,\
		human_corr_oe,\
		count_yn,\
		count_oe\
		))
		self.conn.commit() #submit change to db
		
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
		self.S=self.langDict()
	def sql_word(self,word):
		word=word.lower()
		word=word.replace("'","''")#replace all apostrophes with double for SQL query
		if (re.findall("[a-z]",word) == []) or len(word.split())>1:
			return word
		else:
			return ' '+word #text is already saved with words split from emojis. potential punctuation afterwards
	def parse_date(self,date_range):
		if date_range=='all':
			start_date='2016-03-20 12:00:00'
			end_date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		else:
			start_date=datetime.datetime.strptime(date_range[0], "%B %d, %Y, %H, %M").strftime('%Y-%m-%d %H:%M:%S')
			end_date=datetime.datetime.strptime(date_range[1], "%B %d, %Y, %H, %M").strftime('%Y-%m-%d %H:%M:%S')
		return "AND created_at BETWEEN '{:s}' AND '{:s}'".format(start_date,end_date)
		
	######### Index search result, write to SQL DB ###########################
	def index_result(self, word,freq_filter,face_filter,pattern_type,user_lang,date_range,xdata,ydata):
		word=self.sql_word(word)
		word=word.replace("''","'")#undo all double apostrophes used for SQL query
		if date_range=='all':
			daterange=[datetime.datetime.strptime('2016-03-23 12:00:00','%Y-%m-%d %H:%M:%S'),datetime.datetime.now()]
		else:
			start_date=datetime.datetime.strptime(date_range[0], "%B %d, %Y, %H, %M")
			end_date=datetime.datetime.strptime(date_range[1], "%B %d, %Y, %H, %M")
			daterange=[start_date,end_date]
		self.cur.execute("INSERT INTO emoji_search (\
		date,\
		searchTerm ,\
		emojiLabel,\
		emojiCount,\
		FreqFilter,\
		FaceFilter,\
		PatternType,\
		Lang,\
		daterange\
		)\
		VALUES (\
		%s,%s,%s,%s,%s,%s,%s,%s,%s\
		)",(\
		datetime.datetime.utcnow(),\
		word,\
		xdata,\
		ydata,\
		freq_filter,\
		face_filter,\
		pattern_type,\
		user_lang,\
		daterange,\
		))
		self.conn.commit() #submit change to db
		
	def index_skin_result(self,word,user_lang,date_range,xdata,ydata):
		word=self.sql_word(word)
		word=word.replace("''","'")#undo all double apostrophes used for SQL query
		if date_range=='all':
			daterange=[datetime.datetime.strptime('2016-03-23 12:00:00','%Y-%m-%d %H:%M:%S'),datetime.datetime.now()]
		else:
			start_date=datetime.datetime.strptime(date_range[0], "%B %d, %Y, %H, %M")
			end_date=datetime.datetime.strptime(date_range[1], "%B %d, %Y, %H, %M")
			daterange=[start_date,end_date]
		self.cur.execute("INSERT INTO emoji_skin_search (\
		date,\
		searchTerm ,\
		emojiLabel,\
		emojiCount,\
		Lang,\
		daterange\
		)\
		VALUES (\
		%s,%s,%s,%s,%s,%s\
		)",(\
		datetime.datetime.utcnow(),\
		word,\
		xdata,\
		ydata,\
		user_lang,\
		daterange,\
		))
		self.conn.commit() #submit change to db
	
	######### query SQL code: ################################################
	######### query skin code: ################################################
	def emoji_skin(self, word='dog',user_lang='all',date_range='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
		date_sel = self.parse_date(date_range)
		
		self.cur.execute("SELECT Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiSkinLabel) as Label, unnest(emojiSkinCount) as Freq FROM emoji_tweet WHERE (emojiSkinCountSum>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} )) as T group by Label order by TFreq DESC;".format(word,lang,date_sel))
		result=self.cur.fetchall()
		xdata=[val[0] for val in result]
		ydata=[val[1] for val in result]
		return xdata, ydata
	####### emoji Tweet search ###################################################
	def filter_emoji(self, word='dog',face_filter='off',pattern_type='single',user_lang='all',date_range='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
		date_sel = self.parse_date(date_range)
		
		if face_filter=='off':########## If the face filter is OFF: ################
			if pattern_type=='single':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} )) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
			elif pattern_type=='string':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq FROM emoji_tweet WHERE (emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} )) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang,date_sel))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq FROM emoji_tweet WHERE (emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s})) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang,date_sel))
			else:#return all
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s})) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as Freq, unnest(emojiLabelFaceFilter) as FF FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} )) as T WHERE(T.FF is True) group by T.Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
			elif pattern_type=='string':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq FROM emoji_tweet WHERE (emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang,date_sel))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq FROM emoji_tweet WHERE (emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang,date_sel))
			else:#return all
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]) )) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
		#### Calculate and return the result #####################
		result=self.cur.fetchall()
		xdata=[val[0] for val in result]
		ydata=[val[1] for val in result]
		return xdata, ydata

	def filter_emoji_freq(self,word='dog',face_filter='off',pattern_type='single',user_lang='all',date_range='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
		date_sel = self.parse_date(date_range)
		
		if face_filter=='off':########## If the face filter is OFF: ################
			if pattern_type=='single':
				self.cur.execute("SELECT emojiLabel[1] as label,SUM(emojiCount[1]) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} ) group by label order by Freq DESC limit 15;".format(word,lang,date_sel))
			elif pattern_type=='string':
				self.cur.execute("SELECT emojistrLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet WHERE(emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} ) group by label order by Freq DESC limit 10;".format(word,lang,date_sel))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT emojiPatternLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet WHERE(emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} ) group by label order by Freq DESC limit 10;".format(word,lang,date_sel))
			else:#return all
				self.cur.execute("SELECT Label,SUM(T.Freq) as TFreq From (SELECT unnest(ARRAY[emojiLabel[1],emojistrLabel[1],emojiPatternLabel[1]]) as Label, unnest(ARRAY[emojiCount[1],coalesce(emojistrCount[1],0),coalesce(emojiPatternCount[1],0)]) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s})) as T group by Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT emojiLabel[1] as label,SUM(emojiCount[1]) as Freq FROM emoji_tweet where(emojiLabelFaceFilter[1] is true AND LOWER(text) LIKE '%{:s}%' {:s} {:s}) group by label order by Freq DESC limit 15;".format(word,lang,date_sel))
			elif pattern_type=='string':
				self.cur.execute("SELECT emojistrLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet WHERE(emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False])) group by label order by Freq DESC limit 10;".format(word,lang,date_sel))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT emojiPatternLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet WHERE(emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False])) group by label order by Freq DESC limit 10;".format(word,lang,date_sel))
			else:#return all
				self.cur.execute("SELECT Label,SUM(T.Freq) as TFreq From (SELECT unnest(ARRAY[emojiLabel[1],emojistrLabel[1],emojiPatternLabel[1]]) as Label, unnest(ARRAY[emojiCount[1],coalesce(emojistrCount[1],0),coalesce(emojiPatternCount[1],0)]) as Freq FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]) )) as T group by Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
		#### Calculate and return the result #####################
		result=self.cur.fetchall()
		xdata=[val[0] for val in result]
		ydata=[val[1] for val in result]
		return xdata, ydata
	######## Search Surrounding Text ########################################################
	def filter_emoji_surr(self,word='dog',face_filter='off',pattern_type='single',user_lang='all',date_range='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang,lang2='',''
		else:
			lang,lang2="WHERE( lang='{:s}' )".format(user_lang), "AND lang='{:s}' ".format(user_lang)
		date_sel = self.parse_date(date_range)
		
		if face_filter=='off':########## If the face filter is OFF: ################
			if pattern_type=='single':
				self.cur.execute("SELECT Label,SUM(C) as Freq  from (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as C, unnest(prev_sentence) as prev, unnest(next_sentence) as next FROM emoji_tweet {:s} {:s}) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by Freq DESC limit 15;".format(lang,date_sel,word,word))
			elif pattern_type=='string':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet WHERE (emojistrTypes>0 {:s} {:s})) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,date_sel,word,word))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet WHERE (emojiPatternTypes>0 {:s} {:s})) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,date_sel,word,word))
			else:#return all
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq, unnest(array_cat(prev_sentence,array_cat(emojistr_prev_sentence,emojistr_prev_sentence))) as prev, unnest(array_cat(next_sentence,array_cat(emojistr_next_sentence,emojistr_next_sentence))) as next FROM emoji_tweet {:s} {:s} ) as ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 15;".format(lang,date_sel,word,word))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT Label,SUM(C) as Freq  from (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as C, unnest(emojiLabelFaceFilter) as FF, unnest(prev_sentence) as prev, unnest(next_sentence) as next FROM emoji_tweet {:s} {:s} ) ST WHERE (FF is True AND (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%')) group by Label order by Freq DESC limit 15;".format(lang,date_sel,word,word))
			elif pattern_type=='string':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet WHERE (emojistrTypes>0 {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,date_sel,word,word))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet WHERE (emojiPatternTypes>0 {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,date_sel,word,word))
			else:#return all
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq, unnest(array_cat(prev_sentence,array_cat(emojistr_prev_sentence,emojistr_prev_sentence))) as prev, unnest(array_cat(next_sentence,array_cat(emojistr_next_sentence,emojistr_next_sentence))) as next FROM emoji_tweet WHERE (NOT(emojiLabelFaceFilter @> ARRAY[False]) {:s} {:s} )) as ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 15;".format(lang2,date_sel,word,word))
		#### Calculate and return the result ##########################################
		result=self.cur.fetchall()
		xdata=[val[0] for val in result]
		ydata=[val[1] for val in result]
		return xdata, ydata
		
	########## emoji Stats ##############################################################
	def convert(self,xs):
		if xs==None:
			xs=' '
		try:
			val=self.S[xs]
		except KeyError:
			val=xs
		return val
		
	def emoji_stats(self,word,search_type,sort_by,user_lang,timezone,freq_filter,face_filter,date_range):
		date_sel = self.parse_date(date_range)
		timezone='all'
		timezone_query=''
		if word.lower()=='all':
			word=''
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
		rank_to=20
		column="emojiLabel"
		columnCount="emojiCount"
		FF_cut="WHERE (T.FF is TRUE)"
		if face_filter=='off':
			FF_cut=''
		if search_type=='skin':
			rank_to=6
			column="emojiskinlabel"
			columnCount="emojiskincount"
			FF_cut=''
		elif search_type=='string':
			rank_to=10
			column="emojistrlabel"
			columnCount="emojistrcount"
			FF_cut=''
		elif search_type=='pattern':
			rank_to=10
			column="emojipatternlabel"
			columnCount="emojipatterncount"
			FF_cut=''
		group="zone"
		group_column="time_zone"
		if sort_by=="Language":
			group="lang"
			group_column="lang"
		self.cur.execute("SELECT "+group+" , array_agg(label) as TopEmoji, array_agg(TFreq) as TopCount FROM (SELECT T."+group+", T.Label,SUM(T.Freq) as TFreq, rank() OVER (PARTITION BY "+group+" order by SUM(T.Freq) DESC) From (SELECT "+group_column+" as "+group+", unnest("+column+") as Label, unnest("+columnCount+") as Freq, unnest(emojilabelfacefilter) as FF FROM emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} {:s})) as T ".format(word,lang,timezone_query,date_sel)+FF_cut+" group by T."+group+",T.Label) as Q WHERE Q.rank<=30 group by Q."+group+";")
		result=self.cur.fetchall()
		xdata=[data[0] for data in result]
		topEmojis=[data[1][:rank_to] for data in result]
		topCount=[map(int,data[2][:rank_to]) for data in result]
		topCountSum=[sum(map(int,data[2][:])) for data in result]
		topPercent=[["{:0.1f}".format(num) for num in 100*np.array(map(int,data[2][:rank_to]))/sum(map(int,data[2][:]))] for data in result]
		MAPjson=[{group:self.convert(xs),'emojis':[emj.decode('utf8') for emj in topemojis],'count':count, 'countsum':countsum,'percent':percent} for xs,topemojis,count,countsum,percent in zip(xdata,topEmojis,topCount,topCountSum,topPercent)]
		MAPjsonDumps=[json.dumps(val,ensure_ascii=False) for val in MAPjson] #for inserting into SQL
		#word=self.sql_word(word)
		word=word.replace("''","'")#undo all double apostrophes used for SQL query
		if date_range=='all':
			daterange=[datetime.datetime.strptime('2016-03-23 12:00:00','%Y-%m-%d %H:%M:%S'),datetime.datetime.now()]
		else:
			start_date=datetime.datetime.strptime(date_range[0], "%B %d, %Y, %H, %M")
			end_date=datetime.datetime.strptime(date_range[1], "%B %d, %Y, %H, %M")
			daterange=[start_date,end_date]
		self.cur.execute("INSERT INTO emoji_map (\
		date,\
		searchTerm,\
		rank_to,\
		search_type,\
		sort_by,\
		lang,\
		timezone,\
		MAPjson,\
		FreqFilter,\
		FaceFilter,\
		PatternType,\
		dateRange\
		)\
		VALUES (\
		%s,%s,%s,%s,%s,%s,%s,%s::json[],%s,%s,%s,%s\
		)",(\
		datetime.datetime.utcnow(),\
		word,\
		rank_to,\
		search_type,\
		sort_by,\
		user_lang,\
		timezone,\
		MAPjsonDumps,\
		freq_filter,\
		face_filter,\
		search_type,\
		daterange,\
		))
		self.conn.commit() #submit change to db
		return {"values":MAPjson}
		
	def emoji_stats_indexed(self,word,search_type,sort_by,user_lang,timezone,freq_filter,face_filter,date_range):
		date_sel = self.parse_date(date_range)
		timezone='all'
		if word.lower()=='all':
			word=''
		word=self.sql_word(word)
		rank_to=20
		
		self.cur.execute("SELECT mapjson from emoji_map WHERE (searchTerm='{:s}' AND search_type='{:s}' AND sort_by='{:s}' AND lang='{:}' AND timezone='all' AND FaceFilter='{:s}' AND freqfilter='{:s}' ) order by id DESC limit 1;".format(word,search_type,sort_by,user_lang,face_filter,freq_filter)) #add date search
		data=self.cur.fetchall()
		if len(data)==0:
			return 0
		else:
			return {'values':data[0][0]} #as json string
			
	########## emoji map data ##########################################
	def map_data(self):
		self.cur.execute("SELECT mapjson from emoji_map WHERE (facefilter='on') order by id DESC limit 1;")
		return self.cur.fetchall()
		
	########## emoji visual data ##########################################
	def visual(self,word):
		word=self.sql_word(word)
		self.cur.execute("SELECT emojilabel from emoji_search where searchterm='{:s}' order by id DESC limit 1;".format(word))
		result=self.cur.fetchall()
		source_target=[]
		for source in result[0][0]:
			self.cur.execute("SELECT emojilabel from emoji_search where searchterm=%s order by id DESC limit 1;",(source,))
			results=self.cur.fetchall()
			for val in results[0][0]:
				#print (source,val)
				source_target.append((source.decode('utf-8'),val.decode('utf-8')))
		return [{"source":src,"target":tar,"type":"blah"} for src,tar in source_target]
		
	########## emoji Stats ##############################################################
	def emoji_stats2(self):
		self.cur.execute("SELECT mapjson from emoji_map order by id DESC limit 1;")
		data=self.cur.fetchall()
		return {'values':data[0][0]} #as json string
	
	########## Sample Art ##############################################################
	def sample_art(self):
		#self.cur.execute("SELECT b.text from emoji_tweet a join tweet_dump b on a.tweet_id=b.id WHERE (a.emojiCountSum > 30) order by random() limit 100;")
		self.cur.execute("SELECT b.text from (SELECT * from emoji_tweet TABLESAMPLE SYSTEM ( 0.5)) as a join tweet_dump b on a.tweet_id=b.id WHERE (a.emojiCountSum > 30) limit 100;")
		art=[_u(text[0]) for text in self.cur.fetchall()]
		return '\n\n'.join(art)
		
	def sample_art_options(eCount='>=30',eTypes='>=0',eStrTypes='>=0',ePatTypes='>=0',NL='>=0'):
		self.cur.execute("SELECT text from emoji_tweet WHERE (emojiCountSum {:s} AND emojiTypes {:s} AND emojistrTypes {:s} AND emojiPatternTypes {:s} AND newlineCount {:s}) order by random() limit 100;".format(eCount,eTypes,eStrTypes,ePatTypes,NL))
		
	########## emoji context code ##########################################
	def get_context(self,word,user_lang):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
			
		#self.cur.execute("SELECT text from emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} ) order by random() DESC limit 1000;".format(_u(word),lang))
		self.cur.execute("SELECT text from emoji_tweet TABLESAMPLE SYSTEM ( 20) WHERE (LOWER(text) LIKE '%{:s}%' {:s} ) limit 1000;".format(_u(word),lang))
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
		emoji_key = pd.read_excel(base_dir+'/emojify/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
		emoji_TS = pd.read_excel(base_dir+'/emojify/data/emoji_TS.xlsx', encoding='utf-8', skiprows=1)
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
			TS = _u(file(base_dir+'/emojify/data/lyrics/'+song_list[a]).read())
		except KeyError:
			TS=['']
		return('\n'.join([self.emoji_fy(line,lyric=True) for line in TS.split('\n')]))
	
	def emojifyText(self, a):
		return('\n'.join([self.emoji_fy(line) for line in a.split('\n')]))
	
	def langDict(self):
		S=dict()
		S["all"]="All"
		S["id"]="Bahasa Indonesia - Indonesian"
		S["msa"]="Bahasa Melayu - Malay"
		S["ca"]="Català - Catalan"
		S["cs"]="Čeština - Czech"
		S["da"]="Dansk - Danish"
		S["de"]="Deutsch - German"
		S["en"]="English"
		S["en-gb"]="English UK - British English"
		S["es"]="Español - Spanish"
		S["eu"]="Euskara - Basque (beta)"
		S["fil"]="Filipino"
		S["fr"]="Français - French"
		S["ga"]="Gaeilge - Irish (beta)"
		S["gl"]="Galego - Galician (beta)"
		S["hr"]="Hrvatski - Croatian"
		S["it"]="Italiano - Italian"
		S["xx-lc"]="LOLCATZ - Lolcat (beta)"
		S["hu"]="Magyar - Hungarian"
		S["nl"]="Nederlands - Dutch"
		S["no"]="Norsk - Norwegian"
		S["pl"]="Polski - Polish"
		S["pt"]="Português - Portuguese"
		S["ro"]="Română - Romanian"
		S["sk"]="Slovenčina - Slovak"
		S["fi"]="Suomi - Finnish"
		S["sv"]="Svenska - Swedish"
		S["vi"]="Tiếng Việt - Vietnamese"
		S["tr"]="Türkçe - Turkish"
		S["el"]="Ελληνικά - Greek"
		S["bg"]="Български език - Bulgarian"
		S["ru"]="Русский - Russian"
		S["sr"]="Српски - Serbian"
		S["uk"]="Українська мова - Ukrainian"
		S["he"]="עִבְרִית - Hebrew"
		S["ur"]="اردو - Urdu (beta)"
		S["ar"]="العربية - Arabic"
		S["fa"]="فارسی - Persian"
		S["mr"]="मराठी - Marathi"
		S["hi"]="हिन्दी - Hindi"
		S["bn"]="বাংলা - Bengali"
		S["gu"]="ગુજરાતી - Gujarati"
		S["ta"]="தமிழ் - Tamil"
		S["kn"]="ಕನ್ನಡ - Kannada"
		S["zh-tw"]="繁體中文 - Traditional Chinese"
		S["th"]="ภาษาไทย - Thai"
		S["ko"]="한국어 - Korean"
		S["ja"]="日本語 - Japanese"
		S["zh-cn"]="简体中文 - Simplified Chinese"
		S["cy"]="Welsh"
		S['et']="Estonian"
		S['ht']="Haitian"
		return(S)