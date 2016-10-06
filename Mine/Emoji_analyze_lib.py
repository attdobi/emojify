from __future__ import division
import json
import pandas as pd
import re, collections
import numpy as np
import os, sys
base_dir=os.path.expanduser('~')
import datetime
import time

#read emoji codes:

#base_dir = 'path to emoji_list' #edit this path before use
emoji_key = pd.read_excel(base_dir+'/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" \
           if (code not in emj_codes_skin) if sum([c=="*" for c in code])==0]
#codes that are yellow with the potential for a skin tone
can_have_skin=[key[0:2] for key in emj_codes if re.findall(emj_codes_skin[0],key) != []]
can_have_skin += [key[0:1] for key in emj_codes if len(key[0:2].encode("utf-8"))==6 and re.findall(emj_codes_skin[0],key) != []]
#remove common face emojis
face_index=range(69)
emj_codes_face=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in face_index]

#Not needed in Python 3
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

#remove common face emojis
#face_index=range(69)
#emj_codes_noise=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in face_index]


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

def checkNone(val):
	return val if val else ''
def checkNoneJSON(val):
	return json.dumps(val) if val else '{}'

def analyze_text_emojis(text):
	has_emoji=False
	original_text=text.decode('utf-8')
	#function to quickly scan for has emoji, exit if there is nothing
	for emcode in emj_codes:
		if re.findall(emcode,original_text) != []:
			has_emoji=True
			break
	
	if has_emoji:
	 	#split text using "all" function, then find labels. This counts skin tones properly
		text=emoji_split_all(original_text)
		emojiLabel=np.intersect1d(text.split(),emj_codes,assume_unique=False)
		emjText=np.array([(emcode, text.split().count(emcode)) for emcode in emojiLabel \
			if re.findall(emcode,text)!=[]])
			
		if len(emojiLabel)==0:
			#old, but will work in the case a lone skin tone is used
			emjText=np.array([(emcode, len(re.findall(emcode,text))) for emcode in emj_codes\
				if (re.findall(emcode,text) != [])])
		
		mostFreqWord, mostFreqWordCount = count_words(text)
		newlineCount= text.count('\n')
		#create arrays to save in SQL. Sorted by frequency
		emojiLabel=emjText[np.argsort(emjText[:, 1].astype(int))[::-1]][:,0] #sort by frequency
		#emojiLabelFaceFilter= np.in1d(emojiLabel,emj_codes_face,invert=True)
		emojiCount=np.array(emjText[np.argsort(emjText[:, 1].astype(int))[::-1]][:,1], dtype=int)
		emojiTypes=len(emojiCount)
		emojiCountSum=sum(emojiCount)
		#surrounding_text=surroundingText(text,emojiLabel) #sorted by frequency, using 
		#prev_word=surrounding_text[:,1]
		#next_word=surrounding_text[:,2]
		#prev_sentence=surrounding_text[:,3]
		#next_sentence=surrounding_text[:,4]
		
		#skin tone information
		emjText_skin=[(emcode, len(re.findall(emcode,text))) for emcode in emj_codes_skin\
			if (re.findall(emcode,text) !=[])]
		emjText_skinYellow=np.array([(emcode, text.split().count(emcode)) for emcode in can_have_skin\
			if text.split().count(emcode)>0])
		#note: findall will look for the skin codes in the double unicode singlets. text.split().count will explicitly look for emojois that could have had a skin tone but didn't
		if len(emjText_skinYellow) > 0:#if yellow skin count is non zero then add it
			emjText_skin.append((u'\U0001f590',sum(emjText_skinYellow[:,1].astype(int))))
			#emjText_skin=np.vstack((emjText_skin,np.array([u'\U0001f590',sum(emjText_skinYellow[:,1].astype(int))])))#yellow hand emoji
		
		if len(emjText_skin)==0:
			emojiSkinLabel, emojiSkinCount,emojiSkinCountSum,emojiSkinTypes= [],[],0,0
		else:
			emjText_skin=np.array(emjText_skin)
			#create arrays to save in SQL. Sorted by frequency
			emojiSkinLabel=emjText_skin[np.argsort(emjText_skin[:, 1].astype(int))[::-1]][:,0] 
			emojiSkinCount=np.array(emjText_skin[np.argsort(emjText_skin[:, 1].astype(int))[::-1]][:,1],dtype=int)
			emojiSkinCountSum=sum(emojiSkinCount)
			emojiSkinTypes=len(emojiSkinCount)
	

	
		return(emojiLabel,emojiCount,emojiCountSum,emojiTypes,mostFreqWord,\
	mostFreqWordCount,newlineCount,emojiSkinLabel,emojiSkinCount,emojiSkinCountSum,emojiSkinTypes)
	