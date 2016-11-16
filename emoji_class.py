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
from sklearn.externals import joblib

# guarantee unicode string... #no need in python3 (will cause an error)
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

class TallLabs_lib:
	"""Tall Labs Class"""
	def __init__(self):
		#setup
		self.conn = psycopg2.connect("host=localhost port=5432 dbname=amazon user=postgres password=darkmatter")
		self.cur = self.conn.cursor()
		self.stoplist = set('a an for of the and to in rt'.split())
		self.clf = joblib.load(base_dir+'/TallLabs/models/three_word_logreg_py2.pkl') 
		self.clf_1 = joblib.load(base_dir+'/TallLabs/models/first_word_logreg_py.pkl') 
		self.QmodelB=models.Word2Vec.load(base_dir+'/TallLabs/models/QmodelB')
		self.RmodelB=models.Word2Vec.load(base_dir+'/TallLabs/models/RmodelB_cell')
		self.Rmodel_D2V=models.Doc2Vec.load(base_dir+'/TallLabs/models/Rmodel_Doc2vec_cell')
		self.lda=models.LdaModel.load(base_dir+'/TallLabs/models/lda_cell_15')
		self.dictionary=corpora.Dictionary.load(base_dir+'/TallLabs/models/lda_cell_dict_15')
		self.bag_of_words_yn='is,will,wil,may,might,does,dose,doe,dos,do,can,could,must,should,are,would,do,did'.split(',')
		self.bag_of_words_oe="what,what's,where".split(',')
		self.bag_of_words='is,will,wil,may,might,does,do,can,could,must,should,are,would,did,need,take,out,how,would,am,at,\
anyone,has,have,off,that,which,who,please,thank,you,that,fit,these,they,many,work,with,time,turn,fit,fitt,going,\
from,hard,use,your,not,into,non,hold,say,from,one,two,like,than,same,thanks,find,make,hot,be,as,well,there,\
son,daughter,amazon,when,after,change,both,ask,know,help,me,recently,purchased,item,any,newest,or,come,hi'.split(',')
		self.bag_of_words_verbs='is,will,wil,may,might,does,do,can,could,must,should,are,would,did,take,out,would,\
anyone,off,that,which,who,please,thank,you,that,these,they,many,time,turn,newest,there,am,at,\
from,hard,use,your,not,into,non,hold,say,from,one,two,like,than,same,thanks,\
son,daughter,amazon,when,after,change,both,ask,know,help,me,recently,purchased,item,any,hi'.split(',')
		self.complete_bag=set(sum([[item[0] for item in self.QmodelB.most_similar(word)] for word in self.bag_of_words],[]))|self.stoplist|set(self.bag_of_words)
		self.complete_bag_verbs=set(sum([[item[0] for item in self.QmodelB.most_similar(word)] for word in self.bag_of_words_verbs],[]))|self.stoplist|set(self.bag_of_words_verbs)
		#LDA categories
		self.LDAcategories={0:'Clips, Mounts, Holsters ',1:'Cables, Chargers, Adapters',2:'Batteries, Battery Life',3:'Product Description',\
		4:'USB, Ports, Power',5:'Protective Covers',6:'Prices, Quality',7:'Product Size',\
		8:'Car Accessories, GPS',9:'Screen Protector',10:'Refunds',11:'Bluetooth, Headsets',12:'WaterProof',\
		13:'Camera,Apps',14:'Brands, Models'}
		
	def clean_result(self,model_result):
		return [item[0] for item in model_result],[item[1] for item in model_result]
		#topn=15
	def clean_result_Doc(self,most_sim):
		similar_asins=[val[0].split('R_')[1] for val in most_sim]
		similarity=[val[1] for val in most_sim]
		return similar_asins,similarity
		
	def return_title(self,asin):
		self.cur.execute("SELECT title FROM metadata_cell_phones_and_accessories WHERE asin=%s limit 1;",(asin,))
		return ' '.join(self.cur.fetchall()[0][0].split()[:5])
		
	def visual(self,word,model):
		if model=='reviews':
			modelB=self.RmodelB
		elif model=='questions':
			modelB=self.QmodelB
		else:
			modelB=self.QmodelB
			
		word=word.lower()
		results,counts=self.clean_result(modelB.most_similar(word,topn=5))
		source_target=[]
		for result_word in results:
			#append source target, and search next layer
			source_target.append((word,result_word,1))
			results2,counts2=self.clean_result(modelB.most_similar(result_word,topn=5))
			for result_word2 in results2:
				source_target.append((result_word,result_word2,2))
				results3,counts3=self.clean_result(modelB.most_similar(result_word2,topn=5))
				for result_word3 in results3:
					source_target.append((result_word2,result_word3,3))
		return [{"source":src,"target":tar,"group":grp} for src,tar,grp in source_target]
		
	def tree(self,word,model):
		if model=='reviews':
			modelB=self.RmodelB
		elif model=='questions':
			modelB=self.QmodelB
		else:
			modelB=self.QmodelB
			
		word=word.lower()
		results,counts=self.clean_result(modelB.most_similar(word))
		target=[]
		child_list=[]
		for result_word in results:
			target_child=[]
			target.append(result_word)
			results2,counts2=self.clean_result(modelB.most_similar(result_word))
			for result_word2 in results2:
				target_child.append(result_word2)
			child_list.append(target_child)
		return {"name":word,"children":[{"name":tar,"children":[{"name":child,"size":3} for child in child_l] }\
		 for tar,child_l in zip(target,child_list)]}
		 
	def tree_Doc(self,head_asin,keys):
		modelDoc2vec=self.Rmodel_D2V
		key_words=keys.lower().replace(', ', ',').replace(' ,', ',').replace(' , ', ',').split(',')# form into an array
		key_words_bigram=[word.replace(' ','_') for word in key_words]
		similar_keys=sum([[' '.join(item[0].split('_')) for item in self.check_key(word,'review') if item!=[''] and item[1]>0.7] for word in key_words_bigram],[])
		search_key_vector=modelDoc2vec.infer_vector(key_words+similar_keys,alpha=0) #set alpha to 0 to prevent random permutation
		key='R_'+head_asin
		similar_asins,similarity=self.clean_result_Doc(modelDoc2vec.docvecs.most_similar([key,7*search_key_vector]))
		target=[]
		child_list=[]
		for asin in similar_asins[:5]:
			target_child=[]
			target.append(asin+' , '+self.return_title(asin))
			similar_asins2,similarity2=self.clean_result_Doc(modelDoc2vec.docvecs.most_similar(['R_'+asin,7*search_key_vector]))
			for asin2 in similar_asins2[:5]:
				target_child.append(asin2+' , '+self.return_title(asin2))
			child_list.append(target_child)
		return {"name":head_asin+' , '+self.return_title(head_asin),"children":[{"name":tar,"children":[{"name":child,"size":3} for child in child_l] }\
		 for tar,child_l in zip(target,child_list)]}
		 
	def train(self,input,name):
		self.cur.execute("SELECT qa_id from training order by id DESC limit 1;")
		last_id=self.cur.fetchall()
		self.cur.execute("SELECT id,question,questiontype from qa where id>%s limit 2;",last_id)
		result=self.cur.fetchall()
		qa_id=result[0][0]
		sentence=result[0][1] #returns sentence as a string (could be multiple from one query)
		sentence,first_word = self.process_line_question(sentence) #returns the first sentence and first word
		sentence2=result[1][1] #display this one if the current one is processed
		sentence2,first_word2 = self.process_line_question(sentence2)
		qestion_type=result[0][2]
		
		if input != 'start':
			self.cur.execute("SELECT data_corr_yn,data_corr_oe,bow_corr_yn,bow_corr_oe,count_yn,count_oe from training order by id DESC limit 1;")
			result=self.cur.fetchall()[0]
			data_corr_yn=result[0]
			data_corr_oe=result[1]
			bow_corr_yn=result[2]
			bow_corr_oe=result[3]
			count_yn=result[4]
			count_oe=result[5]
			#check if sentence is in bag of words
			print(self.first_word_in_bag(first_word))
			if self.first_word_in_bag(first_word):
				qestion_type_bow='yes/no'
			else:
				qestion_type_bow='open-ended'
			
			
			if (input == 'yes/no') & (qestion_type_bow =='yes/no'):
				bow_corr_yn= (bow_corr_yn*count_yn+1)/(count_yn+1)
			if (input == 'yes/no') & (qestion_type_bow !='yes/no'):
				bow_corr_yn= (bow_corr_yn*count_yn+0)/(count_yn+1)
			if (input == 'open-ended') & (qestion_type_bow =='open-ended'):
				bow_corr_oe= (bow_corr_oe*count_oe+1)/(count_oe+1)
			if (input == 'open-ended') & (qestion_type_bow !='open-ended'):
				bow_corr_oe= (bow_corr_oe*count_oe+0)/(count_oe+1)
				
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
			self.insert_result(sentence,qestion_type,qestion_type_bow,input,qa_id,data_corr_yn,data_corr_oe,bow_corr_yn,bow_corr_oe,count_yn,count_oe,name)
			sentence=sentence2 #return the next one to display
		return(sentence)
		 
	def train_plot(self):
		self.cur.execute("SELECT data_corr_yn,data_corr_oe,bow_corr_yn,bow_corr_oe from training order by id DESC limit 1;")
		result=self.cur.fetchall()[0]
		print(result)
		yn=[result[0],result[2]]
		oe=[result[1],result[3]]
		key=['Data','BoW']
		label=['Yes/No','Open Ended']
		#print(xx,yy,key)
		return [{"values":[{"y":yn[0]*100,"x":label[0]},{"y":oe[0]*100,"x":label[1]}],"key":key[0],"yAxis":"1"},\
 {"values":[{"y":yn[1]*100,"x":label[0]},{"y":oe[1]*100,"x":label[1]}],"key":key[1],"yAxis":"1"}]
	
	
	def leader_board(self):
		self.cur.execute("SELECT name, count(*) from training group by name order by count DESC;")
		result=self.cur.fetchall()
		#print(result)
		#names = [val[0] for val in result]
		#counts = [val[1] for val in result]
		return {"values":[{"rank":rank+1,"value":count,"label":name} for rank,(name,count) in enumerate(result)],"key": "Serie 1"}
		
	def insert_result(self,question,qestion_type,qestion_type_bow,qestion_type_human,qa_id,data_corr_yn,data_corr_oe,bow_corr_yn,bow_corr_oe,count_yn,count_oe,name):
		self.cur.execute("INSERT INTO training (\
		question,\
		qestion_type,\
		qestion_type_bow,\
		qestion_type_human,\
		qa_id,\
		data_corr_yn,\
		data_corr_oe,\
		bow_corr_yn,\
		bow_corr_oe,\
		count_yn,\
		count_oe,\
		name,\
		time\
		)\
		VALUES (\
		%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\
		)",(\
		question,\
		qestion_type,\
		qestion_type_bow,\
		qestion_type_human,\
		qa_id,\
		data_corr_yn,\
		data_corr_oe,\
		bow_corr_yn,\
		bow_corr_oe,\
		count_yn,\
		count_oe,\
		name,\
		datetime.datetime.now()\
		))
		self.conn.commit() #submit change to db
		
	def process_line(self,sentence):
		#step 1 split if we need to
		sentences=re.split(r'[;:.!?]\s*', sentence)
		result= [re.findall("[a-z-.'0-9]+", sent.lower()) for sent in sentences if \
				re.findall("[a-z-.'0-9]+", sent.lower())!=[]]
		if result==[]:
			result=[['']]
		return result
		
	def process_line_question(self,sentence):
		#step 1, split on question. Use for QA training page
		sentences=re.split(r'[;:.!?]\s*', sentence)
		result= [re.findall("[a-z-.'0-9]+", sent.lower()) for sent in sentences if \
			re.findall("[a-z-.'0-9]+", sent.lower())!=[]]
		#return first sentence and first word
		return ' '.join(result[0])+'?',result[0][0]
		
	def first_word_in_bag(self,first_word):
		try:
			is_in_bag=({first_word}|{item[0] for item in self.QmodelB.most_similar(first_word)})&set(self.bag_of_words_yn)!=set()
		except KeyError:
			is_in_bag=False
			
		#remove open ended question
		if first_word in self.bag_of_words_oe:
			is_in_bag=False
			
		return is_in_bag
		
	def getMeta(self,asin):
		self.cur.execute("select metajson->'imUrl', metajson->'description', title from metadata_cell_phones_and_accessories where asin=%s limit 1;",(asin,))
		result=self.cur.fetchall()[0]
		image=result[0]
		description=result[1]
		title=result[2]
		
		#get the question, only use for demo
		self.cur.execute("SELECT question from qa where asin=%s limit 1;",(asin,))
		result=self.cur.fetchall()[0]
		question=result[0]
		
		#get reviews
		self.cur.execute("select reviewtext from reviews_cell_phones_and_accessories where asin=%s;",(asin,))
		result=self.cur.fetchall()
		formated_reviews='\n\n'.join([val[0] for val in result])
		
		return image,title,description,question,formated_reviews
		
	def findTopic(self,key_words,similar_keys):
		'''Return the LDA vector composition of the topics based on the key words in the search'''
		key_words=[words.replace(' ','_') for words in key_words] #add back for bigram search
		similar_keys=[words.replace(' ','_') for words in similar_keys] #add back for bigram search
		#using the review model
		bow_vector = self.dictionary.doc2bow(key_words+similar_keys)
		lda_np=np.array(self.lda[bow_vector]) #find nearest lda vector topic
		lda_np=lda_np[lda_np[:,1].argsort()[::-1]] #sort by percentage 
		return '\n'.join(['{:.1f}%: '.format(val[1]*100)+self.LDAcategories[val[0]] for val in lda_np][:3])

	def processQuestion(self,asin,question):
		'''Find key words and return the most relevent answer from the review text.
		Using Doc2Vec find the most similar reviews and search for answers there also'''
		question.replace("- "," ").replace(" -"," ") #remove - in questions
		key_words, key_words_action = self.return_key_words(question)
		key_words_bigram=[word.replace(' ','_') for word in key_words]
		similar_keys=sum([[' '.join(item[0].split('_')) for item in self.check_key(word,'review') if item!=[''] and item[1]>0.7] for word in key_words_bigram],[])
		
		topic_text=self.findTopic(key_words,similar_keys)#find LDA topic based on search keys
		
		### pull review data on the asin of the product
		self.cur.execute("select reviewtext from reviews_cell_phones_and_accessories where asin=%s;",(asin,))
		result=self.cur.fetchall() #there are multiple reviews per asin, merge them next
		'''Next find the relavent lines in the review text sorted by number of keyword matches'''
		good_sen,good_qual,good_qual_val=self.find_relevent_sentence(self.merge_review(result),key_words)#+similar keys if nothing is found
		sorted_index=sorted(range(len(good_qual_val)),key=lambda x:good_qual_val[x])[::-1]
		#formatted_answer='\n\n'.join([good_qual[index]+':'+good_sen[index] for index in sorted_index][0:5])
		formatted_answer='\n\n'.join([str(ii+1)+':'+good_sen[index] for ii,index in enumerate(sorted_index)][0:5])
		
		'''Find similar reviews based on the nearest review document vecor and question keys(can cross check with amazon 'similar items' in meta data)'''
		similar_asins,sim_reviews,sim_images,sim_titles,sim_descriptions=self.similarReviews(asin,key_words+similar_keys,1)
		good_sen,good_qual,good_qual_val=self.find_relevent_sentence(sim_reviews[0],key_words)
		sorted_index=sorted(range(len(good_qual_val)),key=lambda x:good_qual_val[x])[::-1]
		formatted_answer_sim='\n\n'.join([str(ii+1)+':'+good_sen[index] for ii,index in enumerate(sorted_index)][0:5])
		
		'''get question type prediction based on logistic regresion model:'''
		words=re.findall("[a-z'0-9]+", question.lower())
		if len(words)>=3:
			try:
				prediction=self.clf.predict(1*self.QmodelB[words[0]]+self.QmodelB[words[1]]+self.QmodelB[words[2]])[0]
			except KeyError:
				preduction=1
		elif (len(words)<3) & (len(words)>0):
			try:
				prediction=self.clf_1.predict(self.QmodelB[words[0]])[0]
			except KeyError:
				preduction=1
		else:
			prediction=1
			
		if prediction==1:
			qType='Yes/No'
		else:
			qType='Open-Ended'
		###### End predict question type ##############################
		
		about_text='Question Type: '+qType + '\n\n'+\
		'Keywords: '+ ', '.join(key_words) + '\n'+\
		'Action Words: '+ ', '.join(key_words_action) + '\n'+\
		'Similar Keys: '+ ', '.join(similar_keys) +'\n\n'+\
		'SubTopics: \n'+ topic_text
		
		return formatted_answer, about_text, formatted_answer_sim,sim_titles[0],sim_images[0]
		
	###### Support functions for porcessQuetion ########################################################################
	def similarReviews(self,asin,key_words,N=1):
		'''Return asin and review text of the the N most reviews based on Doc2vec model
		search for most similar review which also includes Keys and Similar Keys from user's search'''
		model=self.Rmodel_D2V #Doc2Vec model trained on the cell phone and accessory review category
		search_key_vector=model.infer_vector(key_words,alpha=0) #set alpha to 0 to prevent random permutation
		most_sim=model.docvecs.most_similar(['R_'+asin,7*search_key_vector])[:N]
		similar_asins=[val[0].split('R_')[1] for val in most_sim]
		#now get the reviewtext and metadata based on the similar asin
		sim_images,sim_descriptions,sim_titles,sim_reviews=[],[],[],[]
		for sim_asin in similar_asins:
			#Note, change metadata_demo to metadata to get the full set, may be slower
			self.cur.execute("select a.metajson->'imUrl', a.metajson->'description', a.title, b.reviewCat from metadata_cell_phones_and_accessories a\
			join (SELECT asin,string_agg(reviewText,'. ') as reviewCat FROM reviews_cell_phones_and_accessories group by \
			asin) b on a.asin=b.asin where a.asin=%s limit 1;",(sim_asin,))
			result=self.cur.fetchall()[0]
			sim_images.append(result[0])
			sim_descriptions.append(result[1])
			sim_titles.append(result[2])
			sim_reviews.append(result[3])
		return similar_asins,sim_reviews,sim_images,sim_titles,sim_descriptions
		
	def q_filter(self,sentence):
		#filter the question text
		return [word.lower() for word in sum(self.process_line(sentence),[]) if word not in self.complete_bag]
		
	def q_filter_verb(self,sentence):
		return [word.lower() for word in sum(self.process_line(sentence),[]) if word not in self.complete_bag_verbs]
		
	def find_bigrams(self,key_words):
		ii=0
		while ii < len(key_words)-1:
			if key_words[ii]+'_'+key_words[ii+1] in self.QmodelB:
				key_words.insert(ii,key_words[ii]+' '+key_words[ii+1])
				key_words.pop(ii+1)
				key_words.pop(ii+1)
			ii+=1
		return key_words
		
	def return_key_words(self,question):
		question=question.lower()
		key_words_action= self.find_bigrams(self.q_filter_verb(question))
		key_words=self.find_bigrams(self.q_filter(question))
		[key_words_action.remove(word) for word in key_words]
		return key_words, key_words_action
		
	def find_relevent_sentence(self,text,key_words):
		text=text.lower()
		text=text.replace('/',' / ').replace('(',' ( ').replace(')',' ) ')
		good_sen=[]
		good_qual=[]
		good_qual_val=[]
		sentences = re.split(r"(?<![0-9])[.?!;](?![0-9])",text) #whatever delimiters you will need
		for sen in sentences: #this could also be done with regular expression
		#	if(set(key_words) & set(sen.split())): #find the intersection/union
		#		good_sen.append(sen)
		#		good_qual.append(str(len(set(key_words) & set(sen.split())))+'/'+str(len(set(key_words))))
		#		good_qual_val.append(len(set(key_words) & set(sen.split()))/len(set(key_words)))
		#########use regular expression to find the key words###############
			num_key_matches=len([re.findall(' '+word,sen) for word in key_words if len(re.findall(' '+word,sen))>0]) #number of key words matcheds
			if num_key_matches>0:
				good_sen.append(sen)
				good_qual.append(str(num_key_matches)+'/'+str(len(set(key_words))))
				good_qual_val.append(num_key_matches/len(set(key_words)))
			
		return good_sen,good_qual,good_qual_val
		
	def merge_review(self,sql_result):
		reviews=[]
		[reviews.append(review[0]) for review in sql_result]
		return' '.join(reviews)
		
	def check_key(self,word,model='question'):
		#return similar words based on the Question Bigram Model
		if model=='question':
			try:
				return self.QmodelB.most_similar(word,topn=5)
			except KeyError:
				return [['']]
		elif model=='review':
			try:
				return self.RmodelB.most_similar(word,topn=5)
			except KeyError:
				return [['']]
		else:
			return [['']]
	######### END SUPPORT FUNTIONS ####################################
		########################################################################################################
		
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
		self.emjCodes()#setup emoji code variables:: self.emj_codes, self.emj_codes_skin, self.emj_codes_face,self.can_have_skin
		self.S=self.langDict()
		self.Emoji2vec=models.Word2Vec.load(base_dir+'/emojify/data/Emoji2vec') #load Emoji2vec model
	def sql_word(self,word):
		word=word.lower()
		word=word.replace("'","''")#replace all apostrophes with double for SQL query
		if (re.findall("[a-z]",word) == []) or len(word.split())>1:
			return word
		else:
			return ' '+word #text is already saved with words split from emojis. potential punctuation afterwards. force regex to match ' '+word in sentence
	def parse_date(self,date_range):
		if date_range=='all':
			start_date='2016-03-20 12:00:00'
			end_date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			last_id=self.get_last_id()
			return "AND id > {:d}".format(last_id-1000000) #remove the date range cut from the search and look at last 1M entries
		else:
			start_date=datetime.datetime.strptime(date_range[0], "%B %d, %Y, %H, %M").strftime('%Y-%m-%d %H:%M:%S')
			end_date=datetime.datetime.strptime(date_range[1], "%B %d, %Y, %H, %M").strftime('%Y-%m-%d %H:%M:%S')
			return "AND created_at BETWEEN '{:s}' AND '{:s}'".format(start_date,end_date)
			
	def get_last_id(self):
		self.cur.execute("SELECT id from emoji_tweet order by id desc limit 1;")
		last_id= self.cur.fetchall()[0]
		print last_id
		return last_id
		
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
	
	##### search in indexed result ###########################################
	def emoji_indexed(self,word='dog',freq_filter='all',face_filter='off',pattern_type='single',user_lang='all',date_range='all'):
		word=self.sql_word(word)
		#search user_lang='%%' to ignore lang requirement
		self.cur.execute("SELECT emojilabel,emojicount FROM emoji_search WHERE (searchterm='{:s}' AND freqfilter='{:s}' AND facefilter='{:s}' AND patterntype='{:s}' AND lang LIKE '{:s}') ORDER BY coalesce(emojicount[1],0) DESC LIMIT 1;".format(word,freq_filter,face_filter,pattern_type,user_lang))
		result=self.cur.fetchall()
		if len(result)==0:
			self.cur.execute("SELECT emojilabel,emojicount FROM emoji_search WHERE (searchterm='{:s}' AND freqfilter='{:s}' AND facefilter='{:s}' AND patterntype='{:s}' ) ORDER BY coalesce(emojicount[1],0) DESC LIMIT 1;".format(word,freq_filter,face_filter,pattern_type))
			result=self.cur.fetchall()
		if len(result)==0:
			xdata=[]
			ydata=[]
		else:
			xdata=result[0][0]
			ydata=result[0][1]
		return xdata, ydata
		
	def emoji_skin_indexed(self,word='dog',user_lang='all',date_range='all'):
		word=self.sql_word(word)
		#search user_lang='%%' to ignore lang requirement
		self.cur.execute("SELECT emojilabel,emojicount FROM emoji_skin_search WHERE (searchterm='{:s}' AND lang LIKE '{:s}') ORDER BY coalesce(emojicount[1],0) DESC LIMIT 1;".format(word, user_lang))
		result=self.cur.fetchall()
		if len(result)==0: #if nothing was found, then search without the lang requirement 
			self.cur.execute("SELECT emojilabel,emojicount FROM emoji_skin_search WHERE (searchterm='{:s}' ) ORDER BY coalesce(emojicount[1],0) DESC LIMIT 1;".format(word))
			result=self.cur.fetchall()
		if len(result)==0:
			xdata=[]
			ydata=[]
		else:
			xdata=result[0][0]
			ydata=result[0][1]
		return xdata, ydata
		
	######### query skin code: ################################################
	def emoji_skin(self, word='dog',user_lang='all',date_range='all'):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
		date_sel = self.parse_date(date_range)
		
		#Removed TABLESAMPLE SYSTEM (20) ... was getting too slow, replaced with last_id-1000000 which is taken care of by date_sel('all')
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
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as Freq FROM emoji_tweet  WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} )) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
			elif pattern_type=='string':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq FROM emoji_tweet  WHERE (emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} )) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang,date_sel))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq FROM emoji_tweet  WHERE (emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s})) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang,date_sel))
			else:#return all
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq FROM emoji_tweet  WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s})) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as Freq, unnest(emojiLabelFaceFilter) as FF FROM emoji_tweet  WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} )) as T WHERE(T.FF is True) group by T.Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
			elif pattern_type=='string':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq FROM emoji_tweet  WHERE (emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang,date_sel))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq FROM emoji_tweet  WHERE (emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) as T group by T.Label order by TFreq DESC limit 10;".format(word,lang,date_sel))
			else:#return all
				self.cur.execute("SELECT T.Label,SUM(T.Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq FROM emoji_tweet  WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]) )) as T group by T.Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
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
				self.cur.execute("SELECT emojiLabel[1] as label,SUM(emojiCount[1]) as Freq FROM emoji_tweet  WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} ) group by label order by Freq DESC limit 15;".format(word,lang,date_sel))
			elif pattern_type=='string':
				self.cur.execute("SELECT emojistrLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet  WHERE(emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} ) group by label order by Freq DESC limit 10;".format(word,lang,date_sel))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT emojiPatternLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet  WHERE(emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} ) group by label order by Freq DESC limit 10;".format(word,lang,date_sel))
			else:#return all
				self.cur.execute("SELECT Label,SUM(T.Freq) as TFreq From (SELECT unnest(ARRAY[emojiLabel[1],emojistrLabel[1],emojiPatternLabel[1]]) as Label, unnest(ARRAY[emojiCount[1],coalesce(emojistrCount[1],0),coalesce(emojiPatternCount[1],0)]) as Freq FROM emoji_tweet  WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s})) as T group by Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT emojiLabel[1] as label,SUM(emojiCount[1]) as Freq FROM emoji_tweet  where(emojiLabelFaceFilter[1] is true AND LOWER(text) LIKE '%{:s}%' {:s} {:s}) group by label order by Freq DESC limit 15;".format(word,lang,date_sel))
			elif pattern_type=='string':
				self.cur.execute("SELECT emojistrLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet  WHERE(emojistrTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False])) group by label order by Freq DESC limit 10;".format(word,lang,date_sel))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT emojiPatternLabel[1] as label,SUM(emojiStrCount[1]) as Freq FROM emoji_tweet  WHERE(emojiPatternTypes>0 AND LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False])) group by label order by Freq DESC limit 10;".format(word,lang,date_sel))
			else:#return all
				self.cur.execute("SELECT Label,SUM(T.Freq) as TFreq From (SELECT unnest(ARRAY[emojiLabel[1],emojistrLabel[1],emojiPatternLabel[1]]) as Label, unnest(ARRAY[emojiCount[1],coalesce(emojistrCount[1],0),coalesce(emojiPatternCount[1],0)]) as Freq FROM emoji_tweet  WHERE (LOWER(text) LIKE '%{:s}%' {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]) )) as T group by Label order by TFreq DESC limit 15;".format(word,lang,date_sel))
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
				self.cur.execute("SELECT Label,SUM(C) as Freq  from (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as C, unnest(prev_sentence) as prev, unnest(next_sentence) as next FROM emoji_tweet  {:s} {:s}) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by Freq DESC limit 15;".format(lang,date_sel,word,word))
			elif pattern_type=='string':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet  WHERE (emojistrTypes>0 {:s} {:s})) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,date_sel,word,word))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet  WHERE (emojiPatternTypes>0 {:s} {:s})) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,date_sel,word,word))
			else:#return all
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq, unnest(array_cat(prev_sentence,array_cat(emojistr_prev_sentence,emojistr_prev_sentence))) as prev, unnest(array_cat(next_sentence,array_cat(emojistr_next_sentence,emojistr_next_sentence))) as next FROM emoji_tweet  {:s} {:s} ) as ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 15;".format(lang,date_sel,word,word))
		else:############## If the face filter is ON: ####################
			if pattern_type=='single':
				self.cur.execute("SELECT Label,SUM(C) as Freq  from (SELECT unnest(emojiLabel) as Label, unnest(emojiCount) as C, unnest(emojiLabelFaceFilter) as FF, unnest(prev_sentence) as prev, unnest(next_sentence) as next FROM emoji_tweet  {:s} {:s} ) ST WHERE (FF is True AND (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%')) group by Label order by Freq DESC limit 15;".format(lang,date_sel,word,word))
			elif pattern_type=='string':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojistrLabel) as Label, unnest(emojistrCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet  WHERE (emojistrTypes>0 {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,date_sel,word,word))
			elif pattern_type=='pattern':
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(emojiPatternLabel) as Label, unnest(emojiPatternCount) as Freq, unnest(emojistr_prev_sentence) as prev, unnest(emojistr_next_sentence) as next FROM emoji_tweet  WHERE (emojiPatternTypes>0 {:s} {:s} AND NOT(emojiLabelFaceFilter @> ARRAY[False]))) ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 10;".format(lang2,date_sel,word,word))
			else:#return all
				self.cur.execute("SELECT Label,SUM(Freq) as TFreq From (SELECT unnest(array_cat(emojiLabel,array_cat(emojistrLabel,emojiPatternLabel))) as Label, unnest(array_cat(emojiCount,array_cat(emojistrCount,emojiPatternCount))) as Freq, unnest(array_cat(prev_sentence,array_cat(emojistr_prev_sentence,emojistr_prev_sentence))) as prev, unnest(array_cat(next_sentence,array_cat(emojistr_next_sentence,emojistr_next_sentence))) as next FROM emoji_tweet  WHERE (NOT(emojiLabelFaceFilter @> ARRAY[False]) {:s} {:s} )) as ST WHERE (LOWER(prev) LIKE '%{:s}%' OR LOWER(next) LIKE '%{:s}%') group by Label order by TFreq DESC limit 15;".format(lang2,date_sel,word,word))
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
		self.cur.execute("SELECT emojilabel from emoji_search where searchterm='{:s}' ORDER BY coalesce(emojicount[1],0) DESC LIMIT 1;".format(word))
		#searches for largest hit, can order by id and ignore empty ones to get the latest search
		result=self.cur.fetchall()
		source_target=[]
		for source in result[0][0]:
			self.cur.execute("SELECT emojilabel from emoji_search where searchterm=%s ORDER BY coalesce(emojicount[1],0) DESC LIMIT 1;",(source,))
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
		#Removed TABLESAMPLE SYSTEM (0.5) ... was getting too slow, replaced with last_id-1000000
		last_id=self.get_last_id()
		#self.cur.execute("SELECT b.text from emoji_tweet a join tweet_dump b on a.tweet_id=b.id WHERE (a.emojiCountSum > 30) order by random() limit 100;")
		self.cur.execute("SELECT b.text from (SELECT * from emoji_tweet and id > {:d}) as a join tweet_dump b on a.tweet_id=b.id WHERE (a.emojiCountSum > 30) limit 100;".format(last_id-1000000))
		art=[_u(text[0]) for text in self.cur.fetchall()]
		return '\n\n'.join(art)
		
	def sample_art_options(eCount='>=30',eTypes='>=0',eStrTypes='>=0',ePatTypes='>=0',NL='>=0'):
		#Removed TABLESAMPLE SYSTEM (0.5) ... was getting too slow
		last_id=self.get_last_id()
		self.cur.execute("SELECT text from emoji_tweet WHERE (emojiCountSum {:s} AND emojiTypes {:s} AND emojistrTypes {:s} AND emojiPatternTypes {:s} AND newlineCount {:s}) order by random() limit 100;".format(eCount,eTypes,eStrTypes,ePatTypes,NL))
		
	########## emoji context code ##########################################
	def get_context(self,word,user_lang):
		word=self.sql_word(word)
		if user_lang=='all':
			lang=''
		else:
			lang="AND lang='{:s}'".format(user_lang)
			
		#Removed TABLESAMPLE SYSTEM (0.5) ... was getting too slow. replaced with last_id-1000000
		last_id=self.get_last_id()
		#self.cur.execute("SELECT text from emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} ) order by random() DESC limit 1000;".format(_u(word),lang))
		self.cur.execute("SELECT text from emoji_tweet WHERE (LOWER(text) LIKE '%{:s}%' {:s} and id > {:d}) limit 1000;".format(_u(word),lang,last_id-1000000))
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
			xdata,ydata=self.emoji_indexed(word=word,freq_filter='all',face_filter='on',pattern_type='single',user_lang='%%')#no lang option yet, do all
			if xdata==[]: #If not found use word2vec
				xdata,ydata=self.emoji2vec_lookup(word=word,face_filter='on')
			if xdata==[]: #If not found in word2vec lookup frequency in tweet (this may be slow)
				#ignore, this is too slow, return blank
				#xdata,ydata=self.filter_emoji(word=word,face_filter='on')
				#if xdata==[]:#if still empty return nothing
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
		
	#read emoji codes:
	def emjCodes(self):
		emoji_key = pd.read_excel(base_dir+'/emojify/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
		self.emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
		self.emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" \
				   if (code not in self.emj_codes_skin) if sum([c=="*" for c in code])==0]
		#codes that are yellow with the potential for a skin tone
		self.can_have_skin=[key[0:2] for key in self.emj_codes if re.findall(self.emj_codes_skin[0],key) != []]
		self.can_have_skin += [key[0:1] for key in self.emj_codes if len(key[0:2].encode("utf-8"))==6 and re.findall(self.emj_codes_skin[0],key) != []]
		#remove common face emojis
		face_index=range(69)
		self.emj_codes_face=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in face_index]
		
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
		
	#################### Emoji2vec Functions ####################################
	def most_sim_emj(self,most_sim):
		#first do regex search (speed things up)
		#sim_emj=[val for val in most_sim if re.findall('[a-z,0-9]',val[0])==[]]
		#loop through each emoji code and check the values are emoji unicodes (can be slow)
		#sim_emj=[val for val in sim_emj if sum([re.findall(code,val[0]) for code in self.emj_codes],[])!=[]]
		#faster:
		sim_emj=[val for val in most_sim if val[0][0:2] in self.emj_codes or val[0][0:4] in self.emj_codes]
		xdata=[val[0][0:12] for val in sim_emj]#[0:12] limits the output of emoji strings
		ydata=[val[1] for val in sim_emj]
		return xdata,ydata
		
	def emoji2vec_lookup(self,word='dog',face_filter='off',pattern_type='single',user_lang='en',date_range='all'):
		word=word.lower()
		try:
			xdata,ydata = self.most_sim_emj(self.Emoji2vec.most_similar(word,topn=1000))
		except KeyError:
			xdata,ydata =[],[]
		return xdata[:15],ydata[:15]
	
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