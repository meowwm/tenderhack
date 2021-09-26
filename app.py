from flask import Flask
from flask import render_template, url_for, request
import gd as data_analytics



app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/recs", methods=["GET"])
def recs():
    inn = request.args.get("inn")
    rec_regular = data_analytics.module1(inn)
    rec_similar = data_analytics.module2(inn)
    rec_userbased = data_analytics.module3(int(inn))
    return render_template("recs.html", rec_regular=rec_regular, rec_similar=rec_similar, rec_userbased=rec_userbased)
