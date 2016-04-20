from __future__ import division
import json
import tweepy
from tweepy.streaming import StreamListener
import pandas as pd
import re, collections
import numpy as np
import os
base_dir=os.path.expanduser('~')
import datetime
import time
import psycopg2
CONSUMER_KEY = 'JJNPMPuZubIrFIqDNARJRDPDb'
CONSUMER_SECRET = 'd6MlAqrJFcdyJac9aCQpBHPbwGs5eJB8zkTn5wA3tqBLHZgw0b'
OAUTH_TOKEN = '3229899732-piSMFy32Vi0VSyXJX8R9y2qrkr0piesoHXBdI3v'
OAUTH_TOKEN_SECRET = 'Jq9oTRMUjHRgA7NkJLLHIEyjtCRhYiFHdWkpBw28IBtHG'

#connect to postgrSQL
conn = psycopg2.connect("dbname=emoji_db user=postgres password=darkmatter")
cur = conn.cursor()

#read emoji codes:
emoji_key = pd.read_excel(base_dir+'/emojify/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" \
           if (code not in emj_codes_skin) if sum([c=="*" for c in code])==0]
#remove common face emojis
noise_index=range(69)
emj_codes_noise=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in noise_index]

_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

#read emoji codes:
emoji_key = pd.read_excel(base_dir+'/emojify/data/emoji_list.xlsx', encoding='utf-8', index_col=0, skiprows=1)
emj_codes_skin=[code for code,name in zip(emoji_key['Unicode'],emoji_key['Name']) if ('FITZPATRICK' in name)]
emj_codes=[code for code in emoji_key['Unicode'] if code!="Browser" \
           if (code not in emj_codes_skin) if sum([c=="*" for c in code])==0]
#remove common face emojis
noise_index=range(69)
emj_codes_noise=[code for index,code in zip(emoji_key.index,emoji_key['Unicode']) if index in noise_index]

_u = lambda t: t.decode('UTF-8', 'replace') if isinstance(t, str) else t

def get_keys(tweet):
    max_index=0
    max_count=len(tweet['statuses'][max_index].keys())
    
    for ii in range(len(tweet['statuses'])):
        if max_count < len(tweet['statuses'][ii].keys()):
            max_index=ii
            
    return tweet['statuses'][max_index].keys()

def print_tweets_w_emj(T_DF,num=0):
    for item in T_DF['text'][T_DF['emjSum']>=num]:
        print(item)
        
def make_twitter_DF(tweet): #create PD dataframe
    columns=get_keys(tweet)
    for ii in range(len(tweet['statuses'])): 
        diff= list(set(columns)-set(tweet['statuses'][ii].keys()))
        for val in diff:
            tweet['statuses'][ii][val]=""
    return pd.DataFrame([tweet['statuses'][ii] for ii in range(len(tweet['statuses']))], columns=get_keys(tweet)) 

def Search_Word(q):
    # Initiate the connection to Twitter REST API
    twitter = Twitter(auth=OAuth( OAUTH_TOKEN, OAUTH_TOKEN_SECRET, CONSUMER_KEY,  CONSUMER_SECRET))       
    tweet= twitter.search.tweets(q=q,lang='en', result_type='recent',count=200)
    T_DF=make_twitter_DF(tweet)
    
    #long search function, more than 100
    #T_DF=long_search(twitter,q,300)
    
    T_DF['emjText']=[[(emcode, len(re.findall(emcode,T_DF['text'][ii]))) for emcode in emj_codes\
                      if (len(re.findall(emcode,T_DF['text'][ii])) > 0)] for ii in range(len(T_DF))]
    T_DF['emjSum']=[sum([item[1] for item in T_DF['emjText'][ii]]) for ii in range(len(T_DF))]
    T_DF['emjTypes']=[len(T_DF['emjText'][ii]) for ii in range(len(T_DF))]
    T_DF['searchWordSum']=[len(re.findall(q,T_DF['text'][ii].lower())) for ii in range(len(T_DF))]
    return T_DF

def Analyze_Freq(T_DF,emj_per_tweet=1,rep_emj_per_tweet=1, emj_types_per_tweet=1, nword=0):
    DFcut=T_DF[(T_DF['emjSum']>=emj_per_tweet) & (T_DF['searchWordSum']>=nword) \
               & (T_DF['emjTypes']>=emj_types_per_tweet)] 
    
    S=dict()
    for key, value in sum(DFcut['emjText'],[]):
        if value>=rep_emj_per_tweet:
            try:
                S[key] +=value
            except KeyError:
                S[key]=value
        
    return pd.DataFrame([(key,S[key]) for key in S],columns=('emoji','freq'))

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
def write_emoji_usage(tweet,has_emoji):
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

#class MineEmojis:    
def analyze_tweet_emojis(tweet):
    has_emoji=False
    original_text=tweet.text
    text=emoji_split(original_text)
    emjText=np.array([(emcode, len(re.findall(emcode,text))) for emcode in emj_codes\
                      if (len(re.findall(emcode,text)) > 0)])

    if len(emjText) >0:
        print(tweet.text)
        has_emoji=True
        mostFreqWord, mostFreqWordCount = count_words(text)
        newlineCount= text.count('\n')
        #create arrays to save in SQL. Sorted by frequency
        emojiLabel=emjText[np.argsort(emjText[:, 1])[::-1]][:,0] 
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

        #tweet data:
        date= datetime.datetime.utcnow()
        created_at = tweet.created_at
        text = tweet.text
        #keep split text?
        retweet_count = tweet.retweet_count
        favorite_count = tweet.favorite_count
        lang=checkNone(tweet.lang)
        geo = checkNoneJSON(tweet.geo)
        time_zone = checkNone(tweet.user.time_zone)
        coordinates = checkNoneJSON(tweet.coordinates)
        name = checkNone(tweet.user.name)
        user_name = checkNone(tweet.user.screen_name)
        
        insertIntoSQL(date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name,\
    emojiLabel,emojiCount,emojiCountSum,emojiTypes,prev_word,next_word,prev_sentence,next_sentence,mostFreqWord,\
    mostFreqWordCount,newlineCount,emojiSkinLabel,emojiSkinCount,emojiSkinCountSum,emojiSkinTypes,emojistrLabel,\
    emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,emojistr_prev_sentence,\
    emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,emojiPatternTypes)
        
    #write_emoji_usage(tweet,has_emoji)
#class MineEmojis:    
def mine_tweets(tweet):
    #print(tweet.text)
    #has_emoji=True
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
    dumpIntoSQL(date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name)

def dumpIntoSQL(date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name):
    cur.execute("INSERT INTO emoji_tweet_dump (\
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
    
def insertIntoSQL(date,created_at,text,retweet_count,favorite_count,lang,geo,coordinates,time_zone,name,user_name,\
    emojiLabel,emojiCount,emojiCountSum,emojiTypes,prev_word,next_word,prev_sentence,next_sentence,mostFreqWord,\
    mostFreqWordCount,newlineCount,emojiSkinLabel,emojiSkinCount,emojiSkinCountSum,emojiSkinTypes,emojistrLabel,\
    emojistrCount,emojistrLen,emojistrTypes,emojistr_prev_word,emojistr_next_word,emojistr_prev_sentence,\
    emojistr_next_sentence,emojiPatternLabel,emojiPatternCount,emojiPatternLen,emojiPatternTypes):
    cur.execute("INSERT INTO emoji_tweet (\
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
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\
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
    list(emojiLabel),\
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
        
class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    #Mine=MineEmojis()
    def on_status(self, status):
        mine_tweets(status)
        return True
    def on_error(self, status):
        print(status)
		
if __name__ == "__main__":
	try:
		while True:
			l=StdOutListener()
			auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
			auth.set_access_token(OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
			api = tweepy.API(auth)
			myStream = tweepy.Stream(auth = api.auth, listener=l)
			myStream.sample()
	except KeyboardInterrupt:
		pass

