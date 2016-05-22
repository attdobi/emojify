from __future__ import division
import os,sys
base_dir=os.path.expanduser('~')
sys.path.append(base_dir+'/emojify')
sys.path.append(base_dir+'/emojify/Mine')
import numpy as np
from emoji_class import *
import locale
locale.setlocale(locale.LC_ALL, 'en_US')
from nltk.corpus import words
#the full english dict is 200k+ words. Lets use the top 20k for speed (takes about 1 days for 20k)
top20k_en=file('20k.txt').read().split('\n')
top20k_es=np.loadtxt('es.txt',unpack=True,dtype=str)[0][:20000]
top20k_ko=np.loadtxt('ko.txt',unpack=True,dtype=str)[0][:20000]

#initialize emoji class
Emoji=emoji_lib()

#loop through each word in the english language and record result in sql DB

pattern_type = 'single'
freq_filter = 'all'
face_filter = 'on'
user_lang = 'ko'

#for word in words.words(): #full list of 230k
for word in top20k_ko: #top 20k
    word = word.decode('utf-8')
    print(word)
    if freq_filter=='freq':
        xdata, ydata = Emoji.filter_emoji_freq(word,face_filter,pattern_type,user_lang)
    elif freq_filter=='all':
        xdata, ydata = Emoji.filter_emoji(word,face_filter,pattern_type,user_lang)
    else: #surr (surrounding text, takes long to query)
        xdata, ydata = Emoji.filter_emoji_surr(word,face_filter,pattern_type,user_lang)
    #write result to DB
    Emoji.index_result(word,freq_filter,face_filter,pattern_type,user_lang,xdata,ydata)
