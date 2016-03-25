#import os
#base_dir=os.path.expanduser('~')
import numpy as np
from query_mongo import *

from flask import Flask, render_template, request, jsonify
application = Flask(__name__)

@application.route("/")
def index():
    return render_template("index.html")
#    #return "<h1 style='color:blue'>Hello There!</h1>"

@application.route("/_add_numbers")
def add_numbers():
    a = request.args.get('a',type=str)
    TS=emojify()
    #print(TS)
    return jsonify(result=str(a)+TS)
    #a = request.args.get('a', type=str)
    #b = request.args.get('b', 0, type=int)
    #return jsonify(result=str(a))

@application.route("/db")
def print_data():
    word = request.args.get('word')
    xdata, ydata = filter_emoji_freq(word=word.lower())
    #return JSenocde
    return jsonify({"values":[{"value":count,"label":emoji} for count, emoji in zip(ydata,xdata)],"key": "Serie 1"})

@application.route("/word/<word>")
def search(word):
    print(word.title().lower())
    xdata, ydata = filter_emoji(word=word.title().lower())
    #return '<br>'.join(str(row) for row in zip(xdata, ydata ))
    return jsonify({"values":[{"value":count,"label":emoji} for count, emoji in zip(ydata,xdata)],"key": "Serie 1"})

def emojify():
    #TS = open("/home/ubuntu/emojify/lyrics/TS.txt").read()
    TS = open("lyrics/TS.txt").read()
    return TS

if __name__ == "__main__":
    application.run(host='0.0.0.0')
