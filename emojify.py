#import os
#base_dir=os.path.expanduser('~')
from __future__ import division
from flask import Flask, render_template, request, request, jsonify
import numpy as np
from emoji_class import *
import locale
locale.setlocale(locale.LC_ALL, 'en_US')

#initialize emoji class
Emoji=emoji_lib()
Tall=TallLabs_lib()

application = Flask(__name__)

@application.route("/")
def index():
    return render_template("index.html")
#    #return "<h1 style='color:blue'>Hello There!</h1>"
@application.route("/skin")
def skin():
    return render_template("skin.html")
@application.route("/stats")
def stats():
    return render_template("stats.html")
@application.route("/emojify")
def emojify():
    return render_template("emojify.html")
@application.route("/emoji_art")
def emoji_art():
    return render_template("emoji_art.html")
@application.route("/emoji_context")
def emoji_context():
    return render_template("emoji_context.html")
@application.route('/map')
def map():
	return render_template("map.html")
@application.route('/visual')
def force():
	return render_template("force.html")
####### Tall Labs Part ######################
@application.route("/force")
def force():
	return render_template("force.html")	
@application.route("/tree")
def tree():
	return render_template("tree.html")
@application.route("/train")
def train():
	return render_template("train.html")
	
@application.route('/_get_vis')
def _get_vis():
	word = request.args.get('word')
	result=Tall.visual(word)
	return jsonify(result=result)
	
@application.route('/_get_tree')
def _get_tree():
	word = request.args.get('word')
	result=Tall.tree(word)
	return jsonify(result=result)
	
@application.route('/_train')
def _train():
	#word = request.args.get('word')
	res=request.args.get('a')
	print(res)
	result=Tall.train(res)
	return jsonify(result=result)
	
@application.route('/_train_plot')
def _train_plot():
	#word = request.args.get('word')
	result=Tall.train_plot()
	return jsonify(result=result)
###### End Tall Labs Part ########################
	
@application.route('/_get_vis')
def _get_vis():
	word = request.args.get('word')
	result=Emoji.visual(word)
	#print(result)
	return jsonify(result=result)

@application.route('/_getArt')
def getArt():
	return jsonify(result=Emoji.sample_art())

@application.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', '',type=str)
    user_lang = request.args.get('lang')
    #TS=emojify
    return jsonify(result=Emoji.emojifyText(a))
    
@application.route('/_song')
def song():
    a = request.args.get('a', 0,type=str)
    TS=Emoji.emojifyLyrics(a)
    return jsonify(result=TS)

@application.route('/_context')
def context():
    a = request.args.get('a')
    user_lang = request.args.get('lang')
    text=Emoji.get_context(a,user_lang)
    return jsonify(result=text)

@application.route("/db")
def print_data():
	word = request.args.get('word')
	pattern_type = request.args.get('pattern_type')
	freq_filter = request.args.get('freq_filter')
	face_filter = request.args.get('face_filter')
	user_lang = request.args.get('user_lang')
	date_range=request.args.get('date_range')
	date_range=date_range.split(' - ') #split start,end
	if freq_filter=='freq':
		xdata, ydata = Emoji.filter_emoji_freq(word,face_filter,pattern_type,user_lang,date_range)
	elif freq_filter=='all':
		xdata, ydata = Emoji.filter_emoji(word,face_filter,pattern_type,user_lang,date_range)
	else: #surr (surrounding text, takes long to query)
		xdata, ydata = Emoji.filter_emoji_surr(word,face_filter,pattern_type,user_lang,date_range)
	#write result to DB
	Emoji.index_result(word,freq_filter,face_filter,pattern_type,user_lang,date_range,xdata,ydata)
	ysum=sum(ydata)
	#save y data as comma separated 1000s string and return JSON
	ystr=[locale.format("%d", val, grouping=True) for val in ydata]
	return jsonify({"values":[{"rank":rank+1,"value":countstr,"percent":"{:0.2f}".format(count/ysum*100),"label":emoji} for rank,(countstr,count,emoji) in enumerate(zip(ystr,ydata,xdata))],"key": "Serie 1"})

@application.route("/dbskin")
def skin_data():
	word = request.args.get('word')
	user_lang = request.args.get('user_lang')
	date_range=request.args.get('date_range')
	date_range=date_range.split(' - ') #split start,end
	xdata, ydata = Emoji.emoji_skin(word,user_lang,date_range)
	Emoji.index_skin_result(word,user_lang,date_range,xdata,ydata)
	ysum=sum(ydata)
	#save y data as comma separated 1000s string and return JSON
	ystr=[locale.format("%d", val, grouping=True) for val in ydata]
	return jsonify({"values":[{"rank":rank+1,"value":countstr,"percent":"{:0.2f}".format(count/ysum*100),"label":emoji} for rank,(countstr,count,emoji) in enumerate(zip(ystr,ydata,xdata))],"key": "Serie 1"})

@application.route("/dbstats")
def getstats():
	word = request.args.get('word')
	search_type = request.args.get('search_type')
	sort_by = request.args.get('sort_type')
	user_lang = request.args.get('user_lang')
	timezone = ''
	freq_filter = request.args.get('freq_filter')
	face_filter = request.args.get('face_filter')
	date_range=request.args.get('date_range').split(' - ') #split start,end
	result=Emoji.emoji_stats_indexed(word,search_type,sort_by,user_lang,timezone,freq_filter,face_filter,date_range)
	if result==0: #if not indexed then search (takes ~10-20 seconds each)
		result=Emoji.emoji_stats(word,search_type,sort_by,user_lang,timezone,freq_filter,face_filter,date_range)
	return jsonify(result)
  
@application.route("/_report_range")
def report_range():
	daterange=request.args.get('daterange')
	#print(daterange)
	print_data()
	return 0

@application.route("/word/<word>")
def search(word):
    print(word.title().lower())
    xdata, ydata = filter_emoji(emoji_key, word=word.title().lower())
    return '<br>'.join(str(row) for row in zip(xdata, ydata ))
    #return jsonify({"values":[{"value":count,"label":emoji} for count, emoji in zip(ydata,xdata)],"key": "Serie 1"})
    
def emojify():
    #TS = file("/home/ubuntu/emojify/lyrics/TS.txt").read()
    TS = file("lyrics/TS.txt").read()
    return TS

if __name__ == "__main__":
    application.run(host='0.0.0.0')
