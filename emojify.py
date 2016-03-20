#import os
#base_dir=os.path.expanduser('~')

from flask import Flask, render_template, request, request, jsonify
application = Flask(__name__)

@application.route("/")
def index():
    return render_template("index.html")
    #return "<h1 style='color:blue'>Hello There!</h1>"

@application.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', type=str)
    b = request.args.get('b', 0, type=int)
    TS=emojify()
    return jsonify(result=str(a)+TS)

def emojify():
    #TS = file("/home/ubuntu/emojify/lyrics/TS.txt").read()
    TS = file("lyrics/TS.txt").read()
    return TS

if __name__ == "__main__":
    application.run(host='0.0.0.0')
