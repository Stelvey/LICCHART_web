from flask import Flask, redirect, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bar_chart_race as bcr
from matplotlib import pyplot as plt
from helpers import catcher, dataperiod, datatocsv, datatodf, fetch, update, iscsv
from datetime import datetime
import regex as re


app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address
)


@app.errorhandler(429)
def rate_limited(e):
    return catcher(5)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/", methods=["POST"])
@limiter.limit("1/5 seconds")
def submit():
    # Default chart values
    bars = 20
    type = 'months'
    smooth = 0.03
    length = None
    api = 'your_api_key_here'

    # User API
    if request.form.get("api"):
        api = request.form.get("api")

    # User type
    if request.form.get("type"):
        type = request.form.get("type")
        if type not in ['months', 'days']:
            return catcher(3)

    # Get start & end and turn them to timestamps (yeah, I know)
    if request.form.get("start"):
        try:
            start = datetime.strptime(request.form.get("start"), '%Y-%m-%d').date()
        except ValueError:
            return catcher(3)
        print('CUSTOM START: {start}'.format(start=start))
    else:
        start = None

    if request.form.get("end"):
        try:
            end = datetime.strptime(request.form.get("end"), '%Y-%m-%d').date()
        except ValueError:
            return catcher(3)
        if start > end:
            return catcher(1)
        print('CUSTOM END: {end}'.format(end=end))
    else:
        end = None

    # User bars, length, smooth
    if request.form.get("bars"):
        try:
            bars = int(request.form.get("bars"))
        except ValueError:
            return catcher(3)
        if bars > 20 or bars < 1:
            return catcher(3)

    if request.form.get("length"):
        try:
            length = round(float(request.form.get("length")), 2)
        except ValueError:
            return catcher(3)
        if length > 30 or length < 0.1:
            return catcher(3)

    if request.form.get("smooth"):
        try:
            smooth = int(request.form.get("smooth")) / 1000
        except ValueError:
            return catcher(3)
        if smooth > 0.06 or smooth < 0.01:
            return catcher(3)

    # User data (username or csv)
    if request.form.get("user"):
        user = request.form.get("user")
        # 1108290000 is the day Last.fm started storing timestamps
        data = fetch(user, api, 1, None)
        if catcher(data) != None:
            return catcher(data)
    elif request.files['file']:
        file = request.files['file']
        # Make sure filename exists
        if file.filename == '':
            return catcher(2)
        # Make sure it ends with .csv
        if not iscsv(file.filename):
            return catcher(2)
        # Update (and also get user from uploaded data)
        data = update(file, api)
        if catcher(data) != None:
            return catcher(data)
        user = data[0][0].split('#', 1)[1]
    else:
        return catcher(0)

    # CSV data URI to pass to user
    csv_uri = datatocsv(data)
    
    # Delete all scrobbles not in period range
    data = dataperiod(data, start, end)

    # Make DataFrame out of data list
    df = datatodf(data, type)
    if catcher(df) != None:
        return catcher(df)

    # Update some default values
    if length:
        length = round(length * 60000 / len(df))
    else:
        if type == 'months':
            length = 1000
        else:
            length = 100
        
    smooth = round(smooth * length)

    print(df)
    print('Rows: ' + str(len(df)))
    print('Length: ' + str(length))
    print('Smooth: ' + str(smooth))

    # Prepare a figure!
    fig, ax = plt.subplots(figsize = (7, 3.9), dpi = 144)
    # Chart background
    ax.set_facecolor('#1a0933')
    ax.tick_params(labelsize = 8, length = 0)
    # Set grid
    ax.grid(True, axis = 'x', color = '#32fbe2')
    # And make it below everything
    ax.set_axisbelow(True)
    # Remove black borders around chart
    [spine.set_visible(False) for spine in ax.spines.values()]
    # Video background
    fig.patch.set_facecolor('#1a0933')
    # Adjust width (fixes empty spaces)
    fig.subplots_adjust(left = 0.2, right = 0.95)
    # Set artists color
    ax.tick_params(colors='white', which='both')

    # Generate a chart!!!
    mp4_uri = bcr.bar_chart_race(
        df = df,
        fig = fig,
        shared_fontdict = {'color': 'white'},
        n_bars = bars,
        bar_label_size = 4,
        tick_label_size = 8,
        filter_column_colors = True,
        period_length = length,
        steps_per_period = smooth
    )
    # Extracting URI
    mp4_uri = re.search('src="(.*)"', mp4_uri, re.DOTALL).group(1)

    return render_template("result.html", mp4_uri = mp4_uri, csv_uri = csv_uri, user = user)