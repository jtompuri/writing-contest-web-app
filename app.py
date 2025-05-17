from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contests")
def contests():
    return render_template("contests.html")

@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/my_texts")
def my_texts():
    return render_template("my_texts.html")

@app.route("/terms_of_use")
def terms_of_use():
    return render_template("terms_of_use.html")