from __future__ import division
import os, sys
import re, collections
import datetime
import json

import numpy as np
import pandas as pd
import psycopg2

base_dir = os.path.expanduser('~')
YELLOW_TONE = u'\U0001f590'
N_SKIN_TONES = 5

# Read emoji codes:
emoji_key = pd.read_csv(base_dir + '/emojify/data/emoji_list.csv', encoding='utf8',
					    index_col=0, na_filter='')
# Skin tones are the last N elements.
emj_codes_skin = list(emoji_key['Unicode'][-N_SKIN_TONES:])
# Remove the single * emoji. Causes issues with SQL db.
emj_codes = [code for code in emoji_key['Unicode'][:-N_SKIN_TONES] if '*' not in code]
emj_codes_set = set(emj_codes)
# Maximum char size of the emoji codes.
max_char_len = max([len(code) for code in emj_codes])
# Find all yellow tones. Those that do not have a skin tacked on.
tone = emj_codes_skin[0]
# Store as a set.
can_have_skin = set([key.replace(tone, '') for key in emj_codes if tone in key])
# Remove common face emojis, # Original was 69, v4=75, v5=84.
face_index = 91
emj_codes_face = list(emoji_key['Unicode'][:face_index])

# Not needed in Python 3
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t
# Constant for emoji_aplit_all function.
ARG = 'arg**_'

#remove common face emojis
#face_index=range(69)
#emj_codes_noise=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in face_index]


def count_words(text):
	S = collections.defaultdict(lambda:0)
	for word in text.split():
		S[word.lower()] += 1
	return max(S, key=S.get), S[max(S, key=S.get)]

def sort_set_by_length(char_set):
    char_array = np.array(list(char_set))
    char_array_lens = np.array([len(c) for c in char_array])
    idx_sorted_by_len = np.argsort(char_array_lens)[::-1]
    return char_array[idx_sorted_by_len]

def emoji_split_all(text, sorted_overlaps):
    '''add a space before and after the emoji, then remove double spaces. Keep \n'''
    lines = []
    # Change '%' to '%%' for string formatting.
    text = text.replace('%', '%%')

    for line in text.split('\n'):
        line_trimmed = line
        for i, emcode in enumerate(sorted_overlaps):
            if emcode in line:
                line = line.replace(emcode, ' ' + emcode + ' ')
                # Remove string from text by replacing it with a placeholder: 'arg**_i'
                line = line.replace(emcode, '%s%s' % (ARG, i))

        indecies_to_fill = \
            [int(word.split(ARG)[-1]) for word in line.split() if ARG in word]
        line_expresion = \
            ' '.join([word if ARG not in word else '%s' for word in line.split()])
        processed_line = line_expresion % tuple(sorted_overlaps[indecies_to_fill])
        lines.append(processed_line)
    return '\n'.join(lines)

def emoji_split(text, sorted_overlaps):
	''' Add a space before and after the emoji. Do not add space between consecutive emojis unless seperated by a space.
	Remove double spaces. Keep \n'''
	lines = []
	for line in text.split('\n'):
		line = _u(line)
		for emcode in sorted_overlaps:
			if re.findall(emcode, line):
				line = line.replace(emcode, '^%s^' % emcode)
		for skin in emj_codes_skin:
			line = _u(line)
			line = line.replace('^%s' % skin, '%s^' % skin) # Put the skin codes back into place but add a space afterwards
		line = line.replace('^^', '')
		line = line.replace('^', ' ')
		lines.append(' '.join(line.split()))
	return '\n'.join(lines)

def emoji_split_line(line, sorted_overlaps):
	''' Add a space before and after the emoji then remove double spaces, while keeping original spaces between emojis'''
	line = line.replace(' ', '^')
	for emcode in sorted_overlaps:
		if re.findall(emcode,line):
			line = line.replace(emcode, ' %s ' % emcode)
	for skin in emj_codes_skin:
		line = _u(line)
		line = line.replace(' %s' % skin, '%s ' % skin) # Put the skin codes back into place but add a space afterwards
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

def checkNone(val):
	return val if val else ''
def checkNoneJSON(val):
	return json.dumps(val) if val else '{}'

def analyze_tweet_emojis(conn, cur, SQL_return):
	#tweet data:
	has_emoji = False
	tweet_id = SQL_return[0]
	date = datetime.datetime.utcnow() #the date processed
	created_at = SQL_return[2]
	original_text = SQL_return[3].decode('utf-8')
	retweet_count = SQL_return[4]
	favorite_count = SQL_return[5]
	lang = SQL_return[6]
	geo = checkNoneJSON(SQL_return[7])
	coordinates = checkNoneJSON(SQL_return[8])
	time_zone = SQL_return[9]
	name = SQL_return[10]
	user_name = SQL_return[11]
	source = SQL_return[12]
	location = SQL_return[13]

	#function to quickly scan for has emoji
	#for emcode in emj_codes:
	#	if re.findall(emcode, original_text) != []:
	#		has_emoji = True
	#		break

	# Function to quickly scan for has emoji.
	text = original_text
	emoji_set = set()
    # Create and n-gram of possible combinations.
	for i in range(len(text)):
		emoji_set.update({text[i: i + n] for n in range(1, max_char_len + 1) if text[i: i + n] in emj_codes_set})
	emojis_found = emj_codes_set.intersection(emoji_set)

	if emojis_found:
		has_emoji = True

		sorted_overlaps = sort_set_by_length(emojis_found)
	 	# Split text using "all" function, then find labels. This counts skin tones properly.
		text = emoji_split_all(original_text, sorted_overlaps)
		emojiLabel = np.intersect1d(text.split(), list(emojis_found), assume_unique=False)
		emjText = np.array([(emcode, text.split().count(emcode)) for emcode in emojiLabel \
			if re.findall(emcode, text)])

		if len(emojiLabel) == 0:
			# Will work in the case that a lone skin tone is used.
			emjText = np.array([(emcode, len(re.findall(emcode, text))) for emcode in emj_codes \
				if re.findall(emcode, text)])
		
		mostFreqWord, mostFreqWordCount = count_words(text)
		newlineCount = text.count('\n')
		# Create arrays to save in SQL. Sorted by frequency.
		emojiLabel = emjText[np.argsort(emjText[:, 1].astype(int))[::-1]][:, 0] #sort by frequency
		emojiLabelFaceFilter = np.in1d(emojiLabel, emj_codes_face, invert=True)
		emojiCount = np.array(emjText[np.argsort(emjText[:, 1].astype(int))[::-1]][:, 1], dtype=int)
		emojiTypes = len(emojiCount)
		emojiCountSum = sum(emojiCount)
		surrounding_text = surroundingText(text, emojiLabel) #sorted by frequency, using 
		prev_word = surrounding_text[:, 1]
		next_word = surrounding_text[:, 2]
		prev_sentence = surrounding_text[:, 3]
		next_sentence = surrounding_text[:, 4]
		
		# Skin tone information.
		# Ok to loop through each skin code because there are only five.
		emjText_skin = \
			[(emcode, len(re.findall(emcode, text))) for emcode in emj_codes_skin if re.findall(emcode,text)]
		# Look for yellow skin tones.
		emojis_in_text = {emj_code[0] for emj_code in emjText}
		yellow_skins_found = emojis_in_text.intersection(can_have_skin)
		emjText_skinYellow = np.array([(emcode, text.split().count(emcode)) for emcode in yellow_skins_found])
		# note: findall will look for the skin codes in the double unicode singlets. text.split().count will explicitly look for emojois that could have had a skin tone but didn't
		if len(emjText_skinYellow) > 0:#if yellow skin count is non zero then add it
			emjText_skin.append((YELLOW_TONE, sum(emjText_skinYellow[:, 1].astype(int))))
			#emjText_skin=np.vstack((emjText_skin,np.array([u'\U0001f590',sum(emjText_skinYellow[:,1].astype(int))])))#yellow hand emoji
		
		if len(emjText_skin) == 0:
			emojiSkinLabel, emojiSkinCount,emojiSkinCountSum,emojiSkinTypes= [], [], 0, 0
		else:
			emjText_skin = np.array(emjText_skin)
			#create arrays to save in SQL. Sorted by frequency
			emojiSkinLabel = emjText_skin[np.argsort(emjText_skin[:, 1].astype(int))[::-1]][:,0] 
			emojiSkinCount = np.array(emjText_skin[np.argsort(emjText_skin[:, 1].astype(int))[::-1]][:,1],dtype=int)
			emojiSkinCountSum = sum(emojiSkinCount)
			emojiSkinTypes = len(emojiSkinCount)
	
		#split with  this function to analyze the strings, no spaces between emojis
		text = emoji_split(original_text, sorted_overlaps)
		# Build array of emoji strings
		emj_str = \
			np.array([(emj_str, int(len(emj_str) / 2)) for emj_str in sum([''.join([word if word in emojiLabel.tolist()+[' '] \
			else 'T' for word in emoji_split_line(line, sorted_overlaps).split()]).rsplit('T') for line in text.split('\n')],[]) \
			if emj_str != ''])
		
		#analyze emoji strings, cut away length 1 emojis and call new array a:
		if len(emj_str) == 0:
			emojistrLabel,emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,\
			emojistr_prev_sentence,emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,emojiPatternTypes=\
			[],[],[],0,[],[],[],[],[],[],[],0
		else: #try to find strings, but first filter length 1 and those with length 2(with skin codes)
			d = collections.defaultdict(lambda:0)
			for key in emj_str[:,0]:
				if key not in emj_codes:#do not include length 2 emoji codes, flags, skins, etc.
					d[key] += 1
			a = np.array([d.values(),d.keys(), [int(len(key)/2) for key in d.keys()]])
			#Old, remove single emojis and double if skin code is included:
			#skin_cut=~np.bool8(((np.int32(a[2,:]))==2) & (np.array([sum([len(re.findall(emcode,val)) for emcode in emj_codes_skin]) for val in a[1,:]])))
			#multi_cut=(np.int32(a[2,:])>1) & skin_cut
			#a=a[:,multi_cut]

			if len(a[0]) == 0:
				emojistrLabel,emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,\
				emojistr_prev_sentence,emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,\
				emojiPatternTypes =\
				[],[],[],0,[],[],[],[],[],[],[],0

			else:
				sort_index = a.argsort(axis=1)
				emojistrLabel = a[[1,sort_index[0]]][::-1]
				emojistrCount = np.array(a[[0,sort_index[0]]][::-1],dtype=int)
				emojistrLen = np.array(a[[2,sort_index[0]]][::-1],dtype=int)
				emojistrTypes = len(emojistrCount)
				#add emjStr CountSum
				surrounding_str_text = surroundingText(text,emojistrLabel) #sorted by frequency
				emojistr_prev_word = surrounding_str_text[:,1]
				emojistr_next_word = surrounding_str_text[:,2]
				emojistr_prev_sentence = surrounding_str_text[:,3]
				emojistr_next_sentence = surrounding_str_text[:,4]
				#find emoji str patterns
				pattern=np.array([(emcode, len(re.findall(emcode,text))) for emcode in emojistrLabel])
				emojiPatternLabel = pattern[np.argsort(pattern[:, 1])[::-1]][:,0] 
				emojiPatternCount = np.array(pattern[np.argsort(pattern[:, 1])[::-1]][:,1],dtype=int)
				emojiPatternLen = np.array([np.int32(len(val)/2) for val in emojiPatternLabel],dtype=int)
				emojiPatternTypes = len(emojiPatternCount)
	
		insertIntoSQL(conn, cur, tweet_id, date, created_at, text, retweet_count, favorite_count, lang, geo, coordinates,\
			time_zone, name, user_name, source, location,\
			emojiLabel,emojiLabelFaceFilter,emojiCount,emojiCountSum,emojiTypes,prev_word,next_word,prev_sentence,\
			next_sentence,mostFreqWord,mostFreqWordCount,newlineCount,emojiSkinLabel,emojiSkinCount,emojiSkinCountSum,\
			emojiSkinTypes,emojistrLabel,emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,\
			emojistr_prev_sentence,emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,emojiPatternTypes)
	
	#write to has_emoji DB
	has_emoji_SQL(conn,cur,tweet_id, has_emoji, created_at)

def mine_tweets(conn, cur, tweet):
	#print(tweet.text)
	#tweet data:
	#get place data and write as json object
	if tweet.place:
		try:
			tweet.place={"full_name":tweet.place.full_name,"country_code":tweet.place.country_code,"country":tweet.place.country,\
			"place_type":tweet.place.place_type,"coordinates":tweet.place.bounding_box.coordinates,"id":tweet.place.id,"name":tweet.place.name}
		except AttributeError:
			tweet.place={"full_name":tweet.place.full_name,"country_code":tweet.place.country_code,"country":tweet.place.country,\
			"place_type":tweet.place.place_type,"id":tweet.place.id,"name":tweet.place.name}
	
	date = datetime.datetime.utcnow()
	created_at = tweet.created_at
	text = tweet.text
	# Note: There is an issue with favorite_count and retweet_count always being 0.
	#retweet_count = tweet.retweet_count
	retweet_count = tweet._json.get('retweeted_status', {}).get('retweet_count', 0)
	#favorite_count = tweet.favorite_count
	favorite_count = tweet._json.get('retweeted_status', {}).get('favorite_count', 0)
	try:
		lang = checkNone(tweet.lang)
	except AttributeError:
		lang = ''
	#geo = checkNoneJSON(tweet.geo) always null, using place instead
	geo = checkNoneJSON(tweet.place)
	time_zone = checkNone(tweet.user.time_zone)
	# Corrdinates are depricated.
	coordinates = checkNoneJSON(tweet.geo)
	name = checkNone(tweet.user.name)
	user_name = checkNone(tweet.user.screen_name)
	source = checkNone(tweet.source)
	location = checkNone(tweet.user.location)
	twitter_id = checkNone(tweet.id)
	# Note: There is also tweet.user.location which contains non standardized location information.
	#print(date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name)
	dumpIntoSQL(conn,cur,date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name, source, location, twitter_id)
	
def dumpIntoSQL(conn,cur,date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name, source, location, twitter_id):
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
	user_name,\
	source,\
	location,\
	twitter_id\
	)\
	VALUES (\
	%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\
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
	user_name,\
	source,\
	location,\
	twitter_id,\
	))
	conn.commit() #submit change to db

def has_emoji_SQL(conn,cur,tweet_id, has_emoji, created_at):
	cur.execute("INSERT INTO has_emoji (\
	tweet_id,\
	has_emoji,\
	created_at\
	)\
	VALUES (\
	%s,%s,%s\
	)",(\
	tweet_id,\
	has_emoji,\
	created_at,\
	))
	conn.commit() #submit change to db

def insertIntoSQL(conn,cur,tweet_id, date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name,\
	source, location,\
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
	source,\
	location,\
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
	%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\
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
	source,\
	location,\
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
