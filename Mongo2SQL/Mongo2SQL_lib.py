from __future__ import division
import json
import pandas as pd
import re, collections
import numpy as np
import os, sys
base_dir=os.path.expanduser('~')
import datetime
import time
import psycopg2
from pymongo import MongoClient

#read emoji codes:
emoji_key = pd.read_excel(base_dir+'/emojify/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" \
           if (code not in emj_codes_skin) if sum([c=="*" for c in code])==0]
#remove common face emojis
face_index=range(69)
emj_codes_face=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in face_index]

#Not needed in Python 3
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

#read emoji codes:
emoji_key = pd.read_excel(base_dir+'/emojify/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" \
           if (code not in emj_codes_skin) if sum([c=="*" for c in code])==0]
#remove common face emojis
noise_index=range(69)
emj_codes_noise=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in noise_index]


def count_words(text):
	S = collections.defaultdict(lambda:0)
	for word in text.split():
		S[word.lower()]+=1
	return max(S, key=S.get), S[max(S, key=S.get)]

def emoji_split_all(text):
	'''add a space before and after the emoji, then remove double spaces. Keep \n'''
	lines=[]
	for line in text.split('\n'):
		for emcode in emj_codes:
			if (len(re.findall(emcode,line))) > 0:
				line=line.replace(emcode,' '+emcode+' ')
		for skin in emj_codes_skin:
			line=_u(line)
			line=line.replace(' '+skin,skin+' ') #put the skin codes back into place but add a space afterwards
		lines.append(' '.join(line.split()))
	return '\n'.join(lines)

def emoji_split(text):
	'''add a space before and after the emoji. Do not add space between consecutive emojis unless seperated by a space.
	Remove double spaces. Keep \n'''
	lines=[]
	for line in text.split('\n'):
		line=_u(line)
		for emcode in emj_codes:
			if (len(re.findall(emcode,line))) > 0:
				line=line.replace(emcode,'^'+emcode+'^')
		for skin in emj_codes_skin:
			line=_u(line)
			line=line.replace('^'+skin,skin+'^') #put the skin codes back into place but add a space afterwards
		line=line.replace('^^','')
		line=line.replace('^',' ')
		lines.append(' '.join(line.split()))
	return '\n'.join(lines)

def emoji_split_line(line):
	'''Add a space before and after the emoji then remove double spaces, while keeping original spaces between emojis'''
	line=line.replace(' ','^')
	for emcode in emj_codes:
		if (len(re.findall(emcode,line))) > 0:
			line=line.replace(emcode,' '+emcode+' ')
	for skin in emj_codes_skin:
		line=_u(line)
		line=line.replace(' '+skin,skin+' ') #put the skin codes back into place but add a space afterwards
	return ' '.join(line.split())

def NextWord(text,emj):
	try:
		last_index=len(text)-(text[::-1].index(emj[::-1]))-2
	except ValueError:
		last_index=len(text)
	return ''.join(text[last_index+2:].split()[:1])

def surroundingText(text,emojiLabel):
	return np.array([(emcode, ''.join(text[:text.index(emcode)].split()[-1:]),\
					NextWord(text,emcode),\
					' '.join(text[:text.index(emcode)].split()[-7:]),\
					' '.join(text[text.index(emcode)+len(emcode):].split()[:7])) for emcode in emojiLabel\
					  if (len(re.findall(emcode,text)) > 0)])

####################################################################################
def write_emoji_usage(tweet,has_emoji): #old, Mongo usage
	entry = {"date": datetime.datetime.utcnow(),\
			 "created_at": tweet.created_at,\
			 "retweet_count": tweet.retweet_count,\
			 "favorite_count": tweet.favorite_count,\
			 "lang": tweet.lang,\
			 "geo": tweet.geo,\
			 "coordinates": tweet.coordinates,\
			 "time_zone": tweet.user.time_zone,\
			 "name":tweet.user.name, "user_name":tweet.user.screen_name,\
			 "has_emoji":has_emoji}
	emoji_usage.insert_one(entry).inserted_id

def checkNone(val):
	return val if val else ''
def checkNoneJSON(val):
	return json.dumps(val) if val else '{}'

def getMongoTweet(tweet):
    #tweet data:
    tweet_id = 0
    date=tweet['date']
    created_at=tweet['created_at']
    try:
        original_text=tweet['text']
    except KeyError:
        original_text=''
    try:
        has_emoji=tweet['has_emoji']
    except KeyError:
        has_emoji=False
    retweet_count=tweet['retweet_count']
    favorite_count=tweet['favorite_count']
    lang=tweet['lang']
    try:
        geo=checkNoneJSON(tweet['goe'])
    except KeyError:
        geo=checkNoneJSON(tweet['geo'])
    coordinates=checkNoneJSON(tweet['coordinates'])
    try:
        time_zone=tweet['time_zone']
    except KeyError:
        time_zone=''
    try:
        name=tweet['name']
    except KeyError:
        name=''
    try:
        user_name=tweet['user_name']
    except KeyError:
        user_name=''
    
    return tweet_id,date,created_at,original_text,has_emoji,retweet_count,favorite_count,lang,geo,coordinates,\
    time_zone,name,user_name


def analyze_tweet_emojis(conn,cur,SQL_return,Mongo=False):
	#tweet data:
	has_emoji=False

	if Mongo:
		tweet_id,date,created_at,original_text,has_emoji,retweet_count,favorite_count,lang,geo,coordinates,\
		time_zone,name,user_name = getMongoTweet(SQL_return)
	else:
		tweet_id = SQL_return[0]
		date=SQL_return[1]
		created_at=SQL_return[2]
		original_text=SQL_return[3]
		retweet_count=SQL_return[4]
		favorite_count=SQL_return[5]
		lang=SQL_return[6]
		geo=checkNoneJSON(SQL_return[7])
		coordinates=checkNoneJSON(SQL_return[8])
		time_zone=SQL_return[9]
		name=SQL_return[10]
		user_name=SQL_return[11]

	text=emoji_split(original_text)
	emjText=np.array([(emcode, len(re.findall(emcode,text))) for emcode in emj_codes\
					  if (len(re.findall(emcode,text)) > 0)])

	if len(emjText) >0:
		#print(text)
		has_emoji=True
		mostFreqWord, mostFreqWordCount = count_words(text)
		newlineCount= text.count('\n')
		#create arrays to save in SQL. Sorted by frequency
		emojiLabel=emjText[np.argsort(emjText[:, 1])[::-1]][:,0]
		emojiLabelFaceFilter= np.in1d(emojiLabel,emj_codes_face,invert=True)
		emojiCount=np.array(emjText[np.argsort(emjText[:, 1])[::-1]][:,1], dtype=int)
		emojiTypes=len(emojiCount)
		emojiCountSum=sum(emojiCount)
		surrounding_text=surroundingText(text,emojiLabel) #sorted by frequency
		prev_word=surrounding_text[:,1]
		next_word=surrounding_text[:,2]
		prev_sentence=surrounding_text[:,3]
		next_sentence=surrounding_text[:,4]

		#build array of emoji strings
		emj_str = np.array([(emj_str, int(len(emj_str)/2)) for emj_str in sum([''.join([word if word in emj_codes+[' '] \
		else 'T' for word in emoji_split_line(line).split()]).rsplit('T') for line in text.split('\n')],[]) if emj_str != ''])
	
		#analyze emoji strings, cut away length 1 emojis and call new array a:
		if len(emj_str)==0:
			emojistrLabel,emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,\
			emojistr_prev_sentence,emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,emojiPatternTypes=\
			[],[],[],0,[],[],[],[],[],[],[],0
		else: #try to find strings, but first filter length 1 and those with length 2(with skin codes)
			d=collections.defaultdict(lambda:0)
			for key in emj_str[:,0]:
				d[key]+=1
			a=np.array([d.values(),d.keys(),[int(len(key)/2) for key in d.keys()]])
			#remove single emojis and double if skin code is included:
			skin_cut=~np.bool8(((np.int32(a[2,:]))==2) & (np.array([sum([len(re.findall(emcode,val)) for emcode in emj_codes_skin]) for val in a[1,:]])))
			multi_cut=(np.int32(a[2,:])>1) & skin_cut
			a=a[:,multi_cut]

			if len(a[0])==0:
				emojistrLabel,emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,\
				emojistr_prev_sentence,emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,\
				emojiPatternTypes=\
				[],[],[],0,[],[],[],[],[],[],[],0

			else:
				sort_index=a.argsort(axis=1)
				emojistrLabel=a[[1,sort_index[0]]][::-1]
				emojistrCount=np.array(a[[0,sort_index[0]]][::-1],dtype=int)
				emojistrLen=np.array(a[[2,sort_index[0]]][::-1],dtype=int)
				emojistrTypes=len(emojistrCount)
				#add emjStr CountSum
				surrounding_str_text=surroundingText(text,emojistrLabel) #sorted by frequency
				emojistr_prev_word=surrounding_str_text[:,1]
				emojistr_next_word=surrounding_str_text[:,2]
				emojistr_prev_sentence=surrounding_str_text[:,3]
				emojistr_next_sentence=surrounding_str_text[:,4]
				#find emoji str patterns
				pattern=np.array([(emcode, len(re.findall(emcode,text))) for emcode in emojistrLabel])
				emojiPatternLabel=pattern[np.argsort(pattern[:, 1])[::-1]][:,0] 
				emojiPatternCount=np.array(pattern[np.argsort(pattern[:, 1])[::-1]][:,1],dtype=int)
				emojiPatternLen=np.array([np.int32(len(val)/2) for val in emojiPatternLabel],dtype=int)
				emojiPatternTypes=len(emojiPatternCount)

		#skin tone information
		emjText_skin=np.array([(emcode, len(re.findall(emcode,text))) for emcode in emj_codes_skin\
					  if (len(re.findall(emcode,text)) > 0)])
		if len(emjText_skin)==0:
			emojiSkinLabel, emojiSkinCount,emojiSkinCountSum,emojiSkinTypes= [],[],0,0
		else:
			#create arrays to save in SQL. Sorted by frequency
			emojiSkinLabel=emjText_skin[np.argsort(emjText_skin[:, 1])[::-1]][:,0] 
			emojiSkinCount=np.array(emjText_skin[np.argsort(emjText_skin[:, 1])[::-1]][:,1],dtype=int)
			emojiSkinCountSum=sum(emojiSkinCount)
			emojiSkinTypes=len(emojiSkinCount)
	
		insertIntoSQL(conn,cur,tweet_id, date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name,\
	emojiLabel,emojiLabelFaceFilter,emojiCount,emojiCountSum,emojiTypes,prev_word,next_word,prev_sentence,next_sentence,mostFreqWord,\
	mostFreqWordCount,newlineCount,emojiSkinLabel,emojiSkinCount,emojiSkinCountSum,emojiSkinTypes,emojistrLabel,\
	emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,emojistr_prev_sentence,\
	emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,emojiPatternTypes)

	if  not Mongo:
		has_emoji_SQL(conn,cur,tweet_id, has_emoji)

def mine_tweets(conn,cur,tweet,Mongo=False):
	#print(tweet.text)
	if Mongo:
		tweet_id,date,created_at,text,has_emoji,retweet_count,favorite_count,lang,geo,coordinates,\
		time_zone,name,user_name = getMongoTweet(tweet)
		dumpIntoSQL(conn,cur,date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name)
		has_emoji_SQL(conn,cur,tweet_id, has_emoji)
	else:
		getMongoTweet(tweet)
		#tweet data:
		date= datetime.datetime.utcnow()
		created_at = tweet.created_at
		text = tweet.text
		retweet_count = tweet.retweet_count
		favorite_count = tweet.favorite_count
		lang=checkNone(tweet.lang)
		geo = checkNoneJSON(tweet.geo)
		time_zone = checkNone(tweet.user.time_zone)
		coordinates = checkNoneJSON(tweet.coordinates)
		name = checkNone(tweet.user.name)
		user_name = checkNone(tweet.user.screen_name)
		dumpIntoSQL(conn,cur,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name)

def dumpIntoSQL(conn,cur,date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name):
	cur.execute("INSERT INTO tweet_dump (\
	date,\
	created_at,\
	text,\
	retweet_count,\
	favorite_count,\
	lang,\
	geo,\
	coordinates,\
	time_zone,\
	name,\
	user_name\
	)\
	VALUES (\
	%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\
	)",(\
	date,\
	created_at,\
	text,\
	retweet_count,\
	favorite_count,\
	lang,\
	geo,\
	coordinates,\
	time_zone,\
	name,\
	user_name\
	))
	conn.commit() #submit change to db

def has_emoji_SQL(conn,cur,tweet_id, has_emoji):
	cur.execute("INSERT INTO has_emoji (\
	tweet_id,\
	has_emoji\
	)\
	VALUES (\
	%s,%s\
	)",(\
	tweet_id,\
	has_emoji\
	))
	conn.commit() #submit change to db

def insertIntoSQL(conn,cur,tweet_id, date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name,\
	emojiLabel,emojiLabelFaceFilter,emojiCount,emojiCountSum,emojiTypes,prev_word,next_word,prev_sentence,next_sentence,mostFreqWord,\
	mostFreqWordCount,newlineCount,emojiSkinLabel,emojiSkinCount,emojiSkinCountSum,emojiSkinTypes,emojistrLabel,\
	emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,emojistr_prev_sentence,\
	emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,emojiPatternTypes):
	cur.execute("INSERT INTO emoji_tweet (\
	tweet_id,\
	date,\
	created_at,\
	text,\
	retweet_count,\
	favorite_count,\
	lang,\
	geo,\
	coordinates,\
	time_zone,\
	name,\
	user_name,\
	emojiLabel,\
	emojiLabelFaceFilter,\
	emojiCount,\
	emojiCountSum,\
	emojiTypes,\
	prev_word,\
	next_word,\
	prev_sentence,\
	next_sentence,\
	mostFreqWord,\
	mostFreqWordCount,\
	newlineCount,\
	emojiSkinLabel,\
	emojiSkinCount,\
	emojiSkinCountSum,\
	emojiSkinTypes,\
	emojistrLabel,\
	emojistrCount,\
	emojistrLen,\
	emojistrTypes,\
	emojistr_prev_word,\
	emojistr_next_word,\
	emojistr_prev_sentence,\
	emojistr_next_sentence,\
	emojiPatternLabel,\
	emojiPatternCount,\
	emojiPatternLen,\
	emojiPatternTypes\
	)\
	VALUES (\
	%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\
	)",(\
	tweet_id,\
	date,\
	created_at,\
	text,\
	retweet_count,\
	favorite_count,\
	lang,\
	geo,\
	coordinates,\
	time_zone,\
	name,\
	user_name,\
	list(emojiLabel),\
	emojiLabelFaceFilter.tolist(),\
	list(emojiCount),\
	emojiCountSum,\
	emojiTypes,\
	list(prev_word),\
	list(next_word),\
	list(prev_sentence),\
	list(next_sentence),\
	mostFreqWord,\
	mostFreqWordCount,\
	newlineCount,\
	list(emojiSkinLabel),\
	list(emojiSkinCount),\
	emojiSkinCountSum,\
	emojiSkinTypes,\
	list(emojistrLabel),\
	list(emojistrCount),\
	list(emojistrLen),\
	emojistrTypes,\
	list(emojistr_prev_word),\
	list(emojistr_next_word),\
	list(emojistr_prev_sentence),\
	list(emojistr_next_sentence),\
	list(emojiPatternLabel),\
	list(emojiPatternCount),\
	list(emojiPatternLen),\
	emojiPatternTypes\
	))
	conn.commit() #submit change to db

