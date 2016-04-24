from __future__ import division
import pandas as pd
import numpy as np
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer('english')
from string import punctuation
from query_mongo import *

import re, collections

# guarantee unicode string
_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

def words(text):
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
        
def str_stemmer(s):
    return [stemmer.stem(word) for word in s]

def lookup(word,emoji_dict):
    try:
        #return ':'+emoji_dict2[stemmer.stem(word)]+':'
        #return emoji_dict[stemmer.stem(word)]
        return emoji_dict[word]
    except KeyError:
        return ""

def lookup_and_search(word,emj_codes_face,emj_codes_skin,emoji_dict,lyric):
    if word in emoji_dict:
        return emoji_dict[word]
    elif lyric==False:
        xdata,ydata=filter_emoji(emj_codes_face, emj_codes_skin, word=word,face_filter='on')
        if len(xdata)==0:
            return ""
        else:
            return xdata[0] #most frequent
    else:
        return ""
        
def buildDict():
	emoji_key = pd.read_excel('data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
	emoji_TS = pd.read_excel('data/emoji_TS.xlsx', encoding='utf-8', skiprows=1)
	emoji_TS=emoji_TS.replace(np.nan,"") # need to remove nan
	emoji_dict=dict()
	for key, name, annotation,action in zip(emoji_key['Unicode'], emoji_key['Name'], emoji_key['Annotations'], emoji_key['Action']):
		for stem_word in str_stemmer(words(annotation)+words(action)):
		#for stem_word in words(annotation)+words(action):
			emoji_dict[_u(stem_word)]=key
	for word, val in zip(emoji_TS['word'], emoji_TS['emoji']):
		for stem_word in words(word):
			emoji_dict[_u(stem_word)]=val
	return emoji_dict
	
def emoji_fy(text,emj_codes_face,emj_codes_skin,emoji_dict=buildDict(),lyric=False):
    text=_u(text) #ensure unicode encoding
    #print(emoji.emojize(''.join([lookup(word) for word in words(text)])))
    #print(''.join([lookup(word) for word in words(text)])+'\n'+text)
    return text+'\n'+''.join([lookup_and_search(word,emj_codes_face,emj_codes_skin,emoji_dict=emoji_dict,lyric=lyric) for word in words(text)])
    #return [lookup(word) for word in words(text)]
    
def emojifyLyrics(a,emj_codes_face,emj_codes_skin,emoji_dict=buildDict()):
	song_list=dict({"Shake it Off (Taylor Swift)":"ShakeItOff_TS.txt","Boyz n The Hood (Eazy-E)":"Boyz-n-the-Hood.txt","Let it Snow (Frozen)":"Let-It_Go.txt","Lollipop (Lil Wayne)":"Lollipop-LW.txt"})
	TS = file("data/lyrics/"+song_list[a]).read()
	return('\n'.join([emoji_fy(line,emj_codes_face,emj_codes_skin,emoji_dict,lyric=True) for line in TS.split('\n')]).encode('utf-8'))
	
def emojifyText(a,emj_codes_face,emj_codes_skin,emoji_dict=buildDict()):
	return('\n'.join([emoji_fy(line,emj_codes_face,emj_codes_skin,emoji_dict) for line in a.split('\n')]).encode('utf-8'))