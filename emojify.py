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

#Setup Authentication #########################################
from functools import wraps
from flask import request, Response

def check_auth(username, password):
	"""This function is called to check if a username /
	password combination is valid.
	"""
	return username == 'insight' and password == 'demo'

def authenticate():
	"""Sends a 401 response that enables basic auth"""
	return Response(
	'Could not verify your access level for that URL.\n'
	'You have to login with proper credentials', 401,
	{'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		if not auth or not check_auth(auth.username, auth.password):
			return authenticate()
		return f(*args, **kwargs)
	return decorated
############# End Authentication ############################

application = Flask(__name__)

@application.route("/")
def index():
    return render_template("index.html")
#    #return "<h1 style='color:blue'>Hello There!</h1>"
@application.route("/emojivec")
def emojivec():
    return render_template("emojivec.html")
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
@application.route('/web')
def web():
	return render_template("web.html")
####### Tall Labs Part ######################
@application.route("/force")
def force():
	return render_template("force.html")
@application.route("/tree")
def tree():
	return render_template("tree.html")
@application.route("/tree_doc")
def tree_doc():
	return render_template("tree_doc.html")
@application.route("/train")
def train():
	return render_template("train.html")
@application.route("/slides")
def slides():
	return render_template("slides.html")
@application.route("/demo")
#@requires_auth
def demo():
	return render_template("search.html")
	
@application.route('/_get_vis')
def _get_vis():
	word = request.args.get('word')
	model = request.args.get('model')
	result=Tall.visual(word,model)
	return jsonify(result=result)
	
@application.route('/_get_tree')
def _get_tree():
	word = request.args.get('word')
	model = request.args.get('model')
	result=Tall.tree(word,model)
	return jsonify(result=result)
	
@application.route('/_get_tree_doc')
def _get_tree_doc():
	asin = request.args.get('asin')
	keys = request.args.get('keys')
	result=Tall.tree_Doc(asin,keys)
	return jsonify(result=result)
	
@application.route('/_train')
def _train():
	res=request.args.get('a')
	name=request.args.get('name')
	result=Tall.train(res,name)
	return jsonify(result=result)
	
@application.route('/_train_plot')
def _train_plot():
	result=Tall.train_plot()
	return jsonify(result=result)
	
@application.route('/_train_table')
def _train_table():
	result=Tall.leader_board()
	print(result)
	return jsonify(result)
	
@application.route('/_update_item')
def _update_item():
	asin = request.args.get('asin')
	image,title,description,ques,revs=Tall.getMeta(asin)
	return jsonify(image=image,title=title,desc=description,ques=ques,revs=revs)
	
@application.route('/_process_question')
def _process_question():
	question = request.args.get('question')
	asin = request.args.get('asin')
	answers,about_text,similar_answer,title2,image_url2=Tall.processQuestion(asin,question)
	return jsonify(result=answers,about=about_text,similar=similar_answer,title2=title2,image2=image_url2)
	
	
###### End Tall Labs Part ########################
	
@application.route('/_get_web')
def _get_web():
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

@application.route("/_emojivec")
def get_emojivec():
	word = request.args.get('word')
	xdata, ydata=Emoji.emoji2vec_lookup(word=word)
	return jsonify({"values":[{"rank":rank+1,"value":sim,"label":emoji} for rank,(sim,emoji) in enumerate(zip(ydata,xdata))],"key": "Serie 1"})
	
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
