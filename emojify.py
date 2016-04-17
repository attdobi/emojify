#import os
#base_dir=os.path.expanduser('~')
from flask import Flask, render_template, request, request, jsonify
import numpy as np
import pandas as pd
from emoji_class import *

#initialize emoji class
Emoji=emoji_lib()

application = Flask(__name__)

@application.route("/")
def index():
    return render_template("index.html")
#    #return "<h1 style='color:blue'>Hello There!</h1>"
@application.route("/emojify")
def emojify():
    return render_template("emojify.html")
@application.route("/emoji_art")
def emoji_art():
    return render_template("emoji_art.html")

@application.route('/_getArt')
def getArt():
	return jsonify(result=Emoji.sample_art())

@application.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0,type=str)
    #TS=emojify
    return jsonify(result=Emoji.emojifyText(a))
    
@application.route('/_song')
def song():
    a = request.args.get('a', 0,type=str)
    TS=Emoji.emojifyLyrics(a)
    return jsonify(result=TS)

@application.route("/db")
def print_data():
	word = request.args.get('word')
	freq_filter = request.args.get('freq_filter')
	face_filter = request.args.get('face_filter')
	if freq_filter=='on':
		xdata, ydata = Emoji.filter_emoji_freq(word=word.lower(),face_filter=face_filter)
	else:
		xdata, ydata = Emoji.filter_emoji(word=word.lower(),face_filter=face_filter)
	#return JSenocde
	return jsonify({"values":[{"value":count,"label":emoji} for count, emoji in zip(ydata,xdata)],"key": "Serie 1"})

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
