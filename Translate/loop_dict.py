from __future__ import division
import os,sys
import datetime
base=os.path.expanduser('~')
sys.path.append(base+'/emojify')
sys.path.append(base+'/emojify/Mine')
import numpy as np
from emoji_class import *
import locale
locale.setlocale(locale.LC_ALL, 'en_US')
from nltk.corpus import words
#the full english dict is 200k+ words. Lets use the top 20k for speed (takes about 1 days for 20k)
top20k_en=file('20k.txt').read().split('\n')
top20k_es=np.loadtxt('es.txt',unpack=True,dtype=str)[0][:20000]
top20k_ko=np.loadtxt('ko.txt',unpack=True,dtype=str)[0][:20000]
top3k_ja=np.loadtxt('jap3000.txt',unpack=True,dtype=str)

#initialize emoji class
Emoji=emoji_lib()


#read emoji codes:
emoji_key = pd.read_excel(base+'/emojify/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" \
           if (code not in emj_codes_skin) if sum([c=="*" for c in code])==0]
#codes that are yellow with the potential for a skin tone
can_have_skin=[key[0:2] for key in emj_codes if re.findall(emj_codes_skin[0],key) != []]
can_have_skin += [key[0:1] for key in emj_codes if len(key[0:2].encode("utf-8"))==6 and re.findall(emj_codes_skin[0],key) != []]
#remove common face emojis
face_index=range(69)
emj_codes_face=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in face_index]


#loop through each word in the english language and record result in sql DB

pattern_type = 'single'
freq_filter = 'all'
face_filter = 'off'
user_lang = 'ko'
date_range='all'
#Add date range

#for word in words.words(): #full list of 230k
#for word in top3k_ja:
for word in emj_codes:
    #word = word.decode('utf-8')
    print(word)
    if freq_filter=='freq':
        xdata, ydata = Emoji.filter_emoji_freq(word,face_filter,pattern_type,user_lang,date_range)
    elif freq_filter=='all':
        xdata, ydata = Emoji.filter_emoji(word,face_filter,pattern_type,user_lang,date_range)
    else: #surr (surrounding text, takes long to query)
        xdata, ydata = Emoji.filter_emoji_surr(word,face_filter,pattern_type,user_lang,date_range)
    #write result to DB
    Emoji.index_result(word,freq_filter,face_filter,pattern_type,user_lang,date_range,xdata,ydata)
