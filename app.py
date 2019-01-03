'''
The Data Incubator 12-day program milestone demo app
Author: Pablo Vega-Behar
Date: December 2018
Notes:
    1) Borrowed a lot of Alexander Sack's code.
    2) Want to add candlestick chart, if time allows

'''

import requests
import pandas as pd
import re
import io

from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter, CrosshairTool
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8

from flask import Flask, render_template, request, redirect, flash, url_for

# Using Alpha Vantage API to request stock prices.
# Note: Alpha Vantage was suggested by Alexander Sack (online TDI cohort)
# Remember to buy Alex a beer when he visits the NYC TDI office!

# Alpha Vantage examples taken from documentation:
# https://www.alphavantage.co/documentation/

ALPHA_VANTAGE_KEY = 'G6G61O14VLJHVBY3'
AV_API_URL = 'https://www.alphavantage.co/query?function={0}&symbol={1}&outputsize={2}&datatype={3}&apikey=' \
             + ALPHA_VANTAGE_KEY

app = Flask(__name__)
app.secret_key = 'Something unique and secret'

# Get the Alpha Vantage data and populate a pandas dataframe
def alpha_vantage(ticker, function='TIME_SERIES_DAILY', outputsize='compact', datatype='csv'):

    # Notes: 1) datatype csv imports easier into pandas
    #        2) Alpha Vantage allows up to 5 API requests per minute and 500 requests per day

    r = requests.get(AV_API_URL.format(function, ticker, outputsize, datatype))
    if r.status_code == 200:
        # Also thanks to Alex Sack on this one: AV still returns 200 for an invalid ticker.
        # So let's check if 'Error Message' is in the returned text.
        if re.search(r'Error Message', r.text):
            return None

        sio = io.StringIO(r.text)   # Borrowed this one from Alex's code,
        # Note: investigate the io library later, as I'm not familiar with it

        if datatype == 'csv':
            df = pd.read_csv(sio)

        df['timestamp'] = pd.to_datetime(df['timestamp'])

    return df


# Create interactive plot
def create_plot(df, ticker, lines):

    line_map = {
        'open':   {'color': 'blue',   'legend': 'Open'},
        'close':  {'color': 'red',    'legend': 'Adj Close'},
        'high':   {'color': 'orange', 'legend': 'High'},
        'low':    {'color': 'black',  'legend': 'Low'},
    }

    # print(df.head(15))

    title = ticker
    source = ColumnDataSource(df)
    hover_tools = []
    p = figure(plot_width=800, plot_height=300, x_axis_type='datetime', title=title)

    for line in lines:
        if line in df:
            p.line(x='timestamp', y=line, source=source,
                     legend=line_map[line]['legend'], color=line_map[line]['color'])
            hover_tools.append((line_map[line]['legend'], '@' + line))

    p.add_tools(HoverTool(tooltips=hover_tools))
    p.yaxis[0].formatter = NumeralTickFormatter(format="$0.00")
    p.grid.grid_line_color = None

    script, div = components(p)

    return script, div


# Candlestick charts.
# Notes:
# 1) Code below based on # http://perfspy.blogspot.com/2017/03/candlestick-chart-using-boken-without.html
# 2) For now I don't care about having date gaps in the chart (this is just me playing with bokeh in web apps)
def create_candlesctick(df, ticker):
    title = ticker

    df['mid'] = df.apply(lambda x: (x['open'] + x['close'])/2, axis=1)
    df['height'] = df.apply(lambda x: abs(x['close']-x['open']) if x['close'] != x['open'] else 0.001, axis=1)

    inc = df.close > df.open
    dec = df.open > df.close
    width = 0.3

    source_inc = ColumnDataSource(df.loc[inc])
    source_dec = ColumnDataSource(df.loc[dec])
    hover_tools = HoverTool(
        tooltips=[
            ('date', '@date'),
            ('open', '@open'),
            ('close', '@close'),
        ])

    tools = (CrosshairTool(), hover_tools)

    p = figure(plot_width=800, plot_height=300, tools=tools, x_axis_type='datetime', title=title)

    # Style candlesticks:
    p.segment(df.timestamp[inc], df.high[inc], df.timestamp[inc], df.low[inc], color='green')  # Positive return
    p.segment(df.timestamp[dec], df.high[dec], df.timestamp[dec], df.low[dec], color='green')  # Negative return
    p.rect(x='timestamp', y='mid', width=width, height=height, fill_color='green', source=source_inc)  # Positive return
    p.rect(x='timestamp', y='mid', width=width, height=height, fill_color='red', source=source_dec)  # Positive return
    p.yaxis[0].formatter = NumeralTickFormatter(format="$0.00")
    p.grid.grid_line_color = None

    script, div = components(p)

    return script, div


@app.route('/', methods=['GET', 'POST'])
def index():
    # Static resources:
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    plot_script = ""
    plot_div = ""

    # Parse form data
    if request.method == 'POST':
        ticker = request.form.get('ticker').strip().upper()
        close = request.form.get('close')
        opening = request.form.get('open')
        high = request.form.get('high')
        low = request.form.get('low')

        # Get stock info from Alpha Vantage
        df = alpha_vantage(ticker)
        if df is not None:
            plot_script, plot_div = create_plot(df, ticker, [opening, close, high, low])

            # TODO: the function below isn't working, Need to figure out how to get input from multiple forms.
            #  Use the index.html file in /template_tinkering and reference:
            #  https://github.com/thedataincubator/sql_heroku/blob/master/app/templates/index.html#L54
            #plot_script, plot_div = create_candlesctick(df, ticker)
        else:
            flash('Stock ticker not found')
            return redirect(url_for('index'))

    # Render results is available
    html = render_template('index.html',
                           js_resources=js_resources,
                           css_resources=css_resources,
                           plot_script=plot_script,
                           plot_div=plot_div,
                           entries=['AAPL', 'GOOG', 'MSFT'])

    return encode_utf8(html)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True, use_debugger=True, use_reloader=True, passthrough_errors=False, port=33507)
